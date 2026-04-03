from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.baseline_predictor import BasketBaselinePredictor


DEFAULT_TOP_K = 3


def log(message: str) -> None:
    print(f"[train_baseline_model] {message}", flush=True)


def resolve_examples_path() -> Path:
    path = ROOT / "data" / "processed" / "instacart_hidden_item_examples_sample.csv"
    if not path.exists():
        raise FileNotFoundError(
            "Missing processed hidden-item examples. Run scripts/build_training_examples.py first."
        )
    return path


def ensure_models_dir() -> Path:
    output_dir = ROOT / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def parse_list_column(value: str) -> list[int] | list[str]:
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected list value, got: {type(parsed)}")
    return parsed


def load_examples(path: Path) -> pd.DataFrame:
    log(f"Loading examples from {path}...")
    examples = pd.read_csv(path)
    examples["context_product_ids"] = examples["context_product_ids"].apply(parse_list_column)
    examples["context_product_names"] = examples["context_product_names"].apply(parse_list_column)
    return examples


def split_examples(examples: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    log("Creating chronological train/test split from sampled orders...")
    cutoff = examples["order_number"].quantile(0.8)
    train_df = examples[examples["order_number"] <= cutoff].copy()
    test_df = examples[examples["order_number"] > cutoff].copy()

    if train_df.empty or test_df.empty:
        raise ValueError("Train/test split produced an empty partition.")

    return train_df, test_df


def build_product_name_map(examples: pd.DataFrame) -> dict[int, str]:
    name_map = {}
    for _, row in examples.iterrows():
        for product_id, product_name in zip(
            row["context_product_ids"], row["context_product_names"], strict=False
        ):
            name_map[int(product_id)] = str(product_name)
        name_map[int(row["target_product_id"])] = str(row["target_product_name"])
    return name_map


def evaluate_model(
    predictor: BasketBaselinePredictor,
    test_df: pd.DataFrame,
    top_k: int,
) -> dict[str, float | int]:
    log(f"Evaluating top-{top_k} recommendation quality...")
    hit_count = 0
    precision_total = 0.0
    unique_predictions: set[int] = set()

    sample_predictions: list[dict[str, object]] = []
    for _, row in test_df.iterrows():
        context = [int(product_id) for product_id in row["context_product_ids"]]
        target = int(row["target_product_id"])
        predictions = predictor.predict(context, top_k=top_k)
        predicted_ids = [prediction.product_id for prediction in predictions]

        hit = int(target in predicted_ids)
        hit_count += hit
        precision_total += hit / top_k
        unique_predictions.update(predicted_ids)

        if len(sample_predictions) < 5:
            sample_predictions.append(
                {
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
    metrics: dict[str, float | int | list[dict[str, object]]] = {
        "train_rows": 0,  # overwritten by caller after evaluation
        "test_rows": test_size,
        "top_k": top_k,
        "hit_rate_at_k": round(hit_count / test_size, 4),
        "recall_at_k": round(hit_count / test_size, 4),
        "precision_at_k": round(precision_total / test_size, 4),
        "coverage": round(len(unique_predictions) / max(len(predictor.global_counts), 1), 4),
        "sample_predictions": sample_predictions,
    }
    return metrics


def write_artifact(metrics: dict[str, object], output_dir: Path) -> Path:
    output_path = output_dir / "baseline_metrics.json"
    output_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return output_path


def main() -> None:
    examples_path = resolve_examples_path()
    examples = load_examples(examples_path)
    train_df, test_df = split_examples(examples)
    product_names = build_product_name_map(examples)

    predictor = BasketBaselinePredictor().fit(
        contexts=train_df["context_product_ids"],
        targets=train_df["target_product_id"].astype(int),
        product_names=product_names,
    )

    metrics = evaluate_model(predictor, test_df, top_k=DEFAULT_TOP_K)
    metrics["train_rows"] = int(len(train_df))

    output_dir = ensure_models_dir()
    output_path = write_artifact(metrics, output_dir)

    print(f"Train rows: {len(train_df):,}")
    print(f"Test rows: {len(test_df):,}")
    print(f"Hit Rate@{DEFAULT_TOP_K}: {metrics['hit_rate_at_k']}")
    print(f"Precision@{DEFAULT_TOP_K}: {metrics['precision_at_k']}")
    print(f"Recall@{DEFAULT_TOP_K}: {metrics['recall_at_k']}")
    print(f"Coverage: {metrics['coverage']}")
    print(f"Wrote metrics to: {output_path}")


if __name__ == "__main__":
    main()
