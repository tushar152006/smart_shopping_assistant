from __future__ import annotations

import ast
import json
from pathlib import Path
import pickle
import sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.feature_ranker import FeatureRanker
from models.personalized_predictor import PersonalizedBasketPredictor

ARTIFACT_DIR = ROOT / "backend" / "artifacts"


def log(message: str) -> None:
    print(f"[export_model_artifact] {message}", flush=True)


def parse_list_column(value: str) -> list[int] | list[str]:
    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list):
        raise ValueError(f"Expected list value, got: {type(parsed)}")
    return parsed


def load_baskets(use_history: bool = False) -> pd.DataFrame:
    filename = (
        "instacart_user_history_baskets.csv"
        if use_history
        else "instacart_baskets_sample.csv"
    )
    path = ROOT / "data" / "processed" / filename
    log(f"Loading baskets from {path}...")
    baskets = pd.read_csv(path)
    baskets["product_ids"] = baskets["product_ids"].apply(parse_list_column)
    baskets["product_names"] = baskets["product_names"].apply(parse_list_column)
    return baskets


def build_product_catalog(baskets: pd.DataFrame) -> list[dict[str, object]]:
    log("Building product catalog...")
    catalog: dict[int, str] = {}
    for _, row in baskets.iterrows():
        for pid, name in zip(row["product_ids"], row["product_names"]):
            catalog[int(pid)] = str(name)

    log(f"Catalog contains {len(catalog):,} unique products.")
    return [
        {"product_id": pid, "product_name": name}
        for pid, name in sorted(catalog.items(), key=lambda x: x[1])
    ]


def build_sample_users(baskets: pd.DataFrame, limit: int = 20) -> list[dict[str, object]]:
    log("Extracting sample active users for demo...")
    user_counts = baskets["user_id"].value_counts()
    sample_users = []
    for user_id in user_counts.head(limit).index:
        user_baskets = baskets[baskets["user_id"] == user_id]
        total_items = sum(len(pids) for pids in user_baskets["product_ids"])
        # get frequent items
        item_freq: dict[str, int] = {}
        for pnames in user_baskets["product_names"]:
            for name in pnames:
                item_freq[name] = item_freq.get(name, 0) + 1
        top_items = sorted(item_freq.items(), key=lambda x: -x[1])[:5]
        sample_users.append({
            "user_id": int(user_id),
            "order_count": int(len(user_baskets)),
            "total_purchased_items": int(total_items),
            "top_favorites": [item[0] for item in top_items],
        })
    return sample_users


def export_artifact() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    
    # We train on the sample baskets first for lightweight and speedy inference
    baskets = load_baskets(use_history=False)
    
    product_map: dict[int, str] = {}
    for _, row in baskets.iterrows():
        for pid, name in zip(row["product_ids"], row["product_names"]):
            product_map[int(pid)] = str(name)
            
    log("Fitting PersonalizedBasketPredictor...")
    basket_records = [
        {
            "user_id": int(row["user_id"]),
            "order_number": int(row["order_number"]),
            "product_ids": [int(pid) for pid in row["product_ids"]],
        }
        for _, row in baskets.iterrows()
    ]
    predictor = PersonalizedBasketPredictor(history_weight=0.7, rule_weight=0.3)
    predictor.fit(basket_records, product_names=product_map)

    # Save model
    model_path = ARTIFACT_DIR / "predictor.pkl"
    log(f"Saving model to {model_path}...")
    with open(model_path, "wb") as f:
        pickle.dump(predictor, f)

    # Save product catalog
    catalog = build_product_catalog(baskets)
    catalog_path = ARTIFACT_DIR / "products_catalog.json"
    log(f"Saving catalog to {catalog_path}...")
    catalog_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")

    # Save sample users
    sample_users = build_sample_users(baskets)
    users_path = ARTIFACT_DIR / "sample_users.json"
    log(f"Saving sample users to {users_path}...")
    users_path.write_text(json.dumps(sample_users, indent=2), encoding="utf-8")

    log("Artifact export completed successfully!")


if __name__ == "__main__":
    export_artifact()
