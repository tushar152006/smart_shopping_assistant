from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.feature_ranker import FeatureRanker


DEFAULT_TOP_K = 3
USE_HISTORY_DATASET = "--history" in sys.argv
MAX_HISTORY_TRAIN_EXAMPLES = 25_000
MAX_HISTORY_TEST_EXAMPLES = 10_000


def log(message: str) -> None:
    print(f"[train_feature_ranker] {message}", flush=True)


def parse_list_column(value: str) -> list[int] | list[str]:
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected list value, got: {type(parsed)}")
    return parsed


def load_baskets() -> pd.DataFrame:
    filename = (
        "instacart_user_history_baskets.csv"
        if USE_HISTORY_DATASET
        else "instacart_baskets_sample.csv"
    )
    baskets = pd.read_csv(ROOT / "data" / "processed" / filename)
    baskets["product_ids"] = baskets["product_ids"].apply(parse_list_column)
    baskets["product_names"] = baskets["product_names"].apply(parse_list_column)
    return baskets


def load_examples() -> pd.DataFrame:
    filename = (
        "instacart_user_history_examples.csv"
        if USE_HISTORY_DATASET
        else "instacart_hidden_item_examples_sample.csv"
    )
    examples = pd.read_csv(ROOT / "data" / "processed" / filename)
    examples["context_product_ids"] = examples["context_product_ids"].apply(parse_list_column)
    examples["context_product_names"] = examples["context_product_names"].apply(parse_list_column)
    return examples


def split_by_order_number(
    baskets: pd.DataFrame, examples: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    cutoff = examples["order_number"].quantile(0.8)
    train_baskets = baskets[baskets["order_number"] <= cutoff].copy()
    train_examples = examples[examples["order_number"] <= cutoff].copy()
    test_examples = examples[examples["order_number"] > cutoff].copy()
    if USE_HISTORY_DATASET:
        train_examples = train_examples.head(MAX_HISTORY_TRAIN_EXAMPLES).copy()
        test_examples = test_examples.head(MAX_HISTORY_TEST_EXAMPLES).copy()
    return train_baskets, train_examples, test_examples


def build_product_name_map(baskets: pd.DataFrame) -> dict[int, str]:
    name_map = {}
    for _, row in baskets.iterrows():
        for product_id, product_name in zip(row["product_ids"], row["product_names"], strict=False):
            name_map[int(product_id)] = str(product_name)
    return name_map


def build_training_rows(ranker: FeatureRanker, train_examples: pd.DataFrame) -> list[dict[str, float | int]]:
    log("Building candidate features for logistic regression...")
    training_rows: list[dict[str, float | int]] = []
    for _, row in train_examples.iterrows():
        training_rows.extend(
            ranker.build_candidate_rows(
                user_id=int(row["user_id"]),
                order_number=int(row["order_number"]),
                context=[int(product_id) for product_id in row["context_product_ids"]],
                target_product_id=int(row["target_product_id"]),
            )
        )
    return training_rows


def evaluate_model(ranker: FeatureRanker, test_examples: pd.DataFrame, top_k: int) -> dict[str, object]:
    log(f"Evaluating feature ranker top-{top_k} quality...")
    hit_count = 0
    precision_total = 0.0
    unique_predictions: set[int] = set()
    sample_predictions: list[dict[str, object]] = []

    for _, row in test_examples.iterrows():
        predictions = ranker.predict(
            user_id=int(row["user_id"]),
            order_number=int(row["order_number"]),
            context=[int(product_id) for product_id in row["context_product_ids"]],
            top_k=top_k,
        )
        predicted_ids = [prediction.product_id for prediction in predictions]
        target = int(row["target_product_id"])
        hit = int(target in predicted_ids)
        hit_count += hit
        precision_total += hit / top_k
        unique_predictions.update(predicted_ids)

        if len(sample_predictions) < 5:
            sample_predictions.append(
                {
                    "user_id": int(row["user_id"]),
                    "target_product_name": row["target_product_name"],
                    "predictions": [
                        {
                            "product_id": prediction.product_id,
                            "score": prediction.score,
                            "reason": prediction.reason,
                        }
                        for prediction in predictions
                    ],
                }
            )

    test_size = int(len(test_examples))
    return {
        "test_rows": test_size,
        "top_k": top_k,
        "hit_rate_at_k": round(hit_count / test_size, 4),
        "recall_at_k": round(hit_count / test_size, 4),
        "precision_at_k": round(precision_total / test_size, 4),
        "coverage": round(len(unique_predictions) / max(len(ranker.global_counts), 1), 4),
        "sample_predictions": sample_predictions,
    }


def main() -> None:
    baskets = load_baskets()
    examples = load_examples()
    train_baskets, train_examples, test_examples = split_by_order_number(baskets, examples)
    product_names = build_product_name_map(baskets)

    ranker = FeatureRanker().fit(
        baskets=train_baskets[["user_id", "order_number", "product_ids"]].to_dict("records"),
        product_names=product_names,
    )
    training_rows = build_training_rows(ranker, train_examples)
    ranker.fit_ranker(training_rows)
    metrics = evaluate_model(ranker, test_examples, DEFAULT_TOP_K)
    metrics["train_baskets"] = int(len(train_baskets))
    metrics["train_examples"] = int(len(train_examples))
    metrics["train_candidate_rows"] = int(len(training_rows))

    filename = (
        "feature_ranker_metrics_history.json"
        if USE_HISTORY_DATASET
        else "feature_ranker_metrics.json"
    )
    output_path = ROOT / "models" / filename
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Train baskets: {len(train_baskets):,}")
    print(f"Train examples: {len(train_examples):,}")
    print(f"Train candidate rows: {len(training_rows):,}")
    print(f"Test rows: {len(test_examples):,}")
    print(f"Hit Rate@{DEFAULT_TOP_K}: {metrics['hit_rate_at_k']}")
    print(f"Precision@{DEFAULT_TOP_K}: {metrics['precision_at_k']}")
    print(f"Recall@{DEFAULT_TOP_K}: {metrics['recall_at_k']}")
    print(f"Coverage: {metrics['coverage']}")
    print(f"Wrote metrics to: {output_path}")


if __name__ == "__main__":
    main()
