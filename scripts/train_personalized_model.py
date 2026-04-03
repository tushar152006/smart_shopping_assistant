from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.personalized_predictor import PersonalizedBasketPredictor


DEFAULT_TOP_K = 3
USE_HISTORY_DATASET = "--history" in sys.argv


def log(message: str) -> None:
    print(f"[train_personalized_model] {message}", flush=True)


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
    path = ROOT / "data" / "processed" / filename
    baskets = pd.read_csv(path)
    baskets["product_ids"] = baskets["product_ids"].apply(parse_list_column)
    baskets["product_names"] = baskets["product_names"].apply(parse_list_column)
    return baskets


def load_examples() -> pd.DataFrame:
    filename = (
        "instacart_user_history_examples.csv"
        if USE_HISTORY_DATASET
        else "instacart_hidden_item_examples_sample.csv"
    )
    path = ROOT / "data" / "processed" / filename
    examples = pd.read_csv(path)
    examples["context_product_ids"] = examples["context_product_ids"].apply(parse_list_column)
    examples["context_product_names"] = examples["context_product_names"].apply(parse_list_column)
    return examples


def split_by_order_number(
    baskets: pd.DataFrame, examples: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    log("Creating chronological train/test split...")
    cutoff = examples["order_number"].quantile(0.8)
    train_baskets = baskets[baskets["order_number"] <= cutoff].copy()
    test_examples = examples[examples["order_number"] > cutoff].copy()
    return train_baskets, test_examples


def build_product_name_map(baskets: pd.DataFrame) -> dict[int, str]:
    name_map = {}
    for _, row in baskets.iterrows():
        for product_id, product_name in zip(row["product_ids"], row["product_names"], strict=False):
            name_map[int(product_id)] = str(product_name)
    return name_map


def evaluate_model(
    predictor: PersonalizedBasketPredictor, test_df: pd.DataFrame, top_k: int
) -> dict[str, object]:
    log(f"Evaluating personalized top-{top_k} quality...")
    hit_count = 0
    precision_total = 0.0
    unique_predictions: set[int] = set()
    sample_predictions: list[dict[str, object]] = []

    for _, row in test_df.iterrows():
        predictions = predictor.predict(
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
                    "context_product_names": row["context_product_names"][:5],
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

    test_size = int(len(test_df))
    return {
        "test_rows": test_size,
        "top_k": top_k,
        "hit_rate_at_k": round(hit_count / test_size, 4),
        "recall_at_k": round(hit_count / test_size, 4),
        "precision_at_k": round(precision_total / test_size, 4),
        "coverage": round(
            len(unique_predictions)
            / max(len(predictor.rule_predictor.global_counts), 1),
            4,
        ),
        "sample_predictions": sample_predictions,
    }


def write_artifact(metrics: dict[str, object]) -> Path:
    filename = (
        "personalized_metrics_history.json"
        if USE_HISTORY_DATASET
        else "personalized_metrics.json"
    )
    output_path = ROOT / "models" / filename
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    baskets = load_baskets()
    examples = load_examples()
    train_baskets, test_examples = split_by_order_number(baskets, examples)
    product_names = build_product_name_map(baskets)

    predictor = PersonalizedBasketPredictor().fit(
        baskets=train_baskets[["user_id", "order_number", "product_ids"]].to_dict("records"),
        product_names=product_names,
    )

    metrics = evaluate_model(predictor, test_examples, DEFAULT_TOP_K)
    metrics["train_baskets"] = int(len(train_baskets))
    metrics["users_with_history"] = int(train_baskets["user_id"].nunique())

    output_path = write_artifact(metrics)
    print(f"Train baskets: {len(train_baskets):,}")
    print(f"Test rows: {len(test_examples):,}")
    print(f"Users with history: {metrics['users_with_history']:,}")
    print(f"Hit Rate@{DEFAULT_TOP_K}: {metrics['hit_rate_at_k']}")
    print(f"Precision@{DEFAULT_TOP_K}: {metrics['precision_at_k']}")
    print(f"Recall@{DEFAULT_TOP_K}: {metrics['recall_at_k']}")
    print(f"Coverage: {metrics['coverage']}")
    print(f"Wrote metrics to: {output_path}")


if __name__ == "__main__":
    main()
