from __future__ import annotations

import ast
import argparse
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.feature_ranker import FeatureRanker


DEFAULT_TOP_K = 3
MAX_HISTORY_TRAIN_EXAMPLES = 25_000
MAX_HISTORY_TEST_EXAMPLES = 10_000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true", help="Use the user-history dataset.")
    parser.add_argument(
        "--train-limit",
        type=int,
        default=None,
        help="Optional cap on the number of train examples after chronological splitting.",
    )
    parser.add_argument(
        "--test-limit",
        type=int,
        default=None,
        help="Optional cap on the number of test examples after chronological splitting.",
    )
    parser.add_argument(
        "--output-suffix",
        default="",
        help="Optional suffix appended to the metrics filename before .json.",
    )
    return parser.parse_args()


def log(message: str) -> None:
    print(f"[train_feature_ranker] {message}", flush=True)


def parse_list_column(value: str) -> list[int] | list[str]:
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected list value, got: {type(parsed)}")
    return parsed


def load_baskets(use_history_dataset: bool) -> pd.DataFrame:
    filename = (
        "instacart_user_history_baskets.csv"
        if use_history_dataset
        else "instacart_baskets_sample.csv"
    )
    baskets = pd.read_csv(ROOT / "data" / "processed" / filename)
    baskets["product_ids"] = baskets["product_ids"].apply(parse_list_column)
    baskets["product_names"] = baskets["product_names"].apply(parse_list_column)
    return baskets


def load_examples(use_history_dataset: bool) -> pd.DataFrame:
    filename = (
        "instacart_user_history_examples.csv"
        if use_history_dataset
        else "instacart_hidden_item_examples_sample.csv"
    )
    examples = pd.read_csv(ROOT / "data" / "processed" / filename)
    examples["context_product_ids"] = examples["context_product_ids"].apply(parse_list_column)
    examples["context_product_names"] = examples["context_product_names"].apply(parse_list_column)
    return examples


def split_by_order_number(
    baskets: pd.DataFrame,
    examples: pd.DataFrame,
    use_history_dataset: bool,
    train_limit: int | None,
    test_limit: int | None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cutoff = examples["order_number"].quantile(0.8)
    train_baskets = baskets[baskets["order_number"] <= cutoff].copy()
    train_examples = examples[examples["order_number"] <= cutoff].copy()
    test_examples = examples[examples["order_number"] > cutoff].copy()
    if use_history_dataset:
        effective_train_limit = (
            train_limit if train_limit is not None else MAX_HISTORY_TRAIN_EXAMPLES
        )
        effective_test_limit = (
            test_limit if test_limit is not None else MAX_HISTORY_TEST_EXAMPLES
        )
        train_examples = train_examples.head(effective_train_limit).copy()
        test_examples = test_examples.head(effective_test_limit).copy()
    else:
        if train_limit is not None:
            train_examples = train_examples.head(train_limit).copy()
        if test_limit is not None:
            test_examples = test_examples.head(test_limit).copy()
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
    args = parse_args()
    baskets = load_baskets(args.history)
    examples = load_examples(args.history)
    train_baskets, train_examples, test_examples = split_by_order_number(
        baskets,
        examples,
        use_history_dataset=args.history,
        train_limit=args.train_limit,
        test_limit=args.test_limit,
    )
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
    metrics["dataset_variant"] = "history" if args.history else "sample"
    metrics["train_limit"] = int(len(train_examples))
    metrics["test_limit"] = int(len(test_examples))

    filename = (
        "feature_ranker_metrics_history"
        if args.history
        else "feature_ranker_metrics"
    )
    if args.output_suffix:
        filename = f"{filename}_{args.output_suffix}"
    output_path = ROOT / "models" / f"{filename}.json"
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
