from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd


MIN_PRIOR_ORDERS = 3
TARGET_USERS = 2_000


def log(message: str) -> None:
    print(f"[build_user_history_training_data] {message}", flush=True)


def resolve_data_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    candidates = [root / "data" / "raw" / "instacart", root / "data" / "raw"]
    expected = {"orders.csv", "order_products__prior.csv", "products.csv"}
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            existing = {path.name for path in candidate.iterdir() if path.is_file()}
            if expected.issubset(existing):
                return candidate
    raise FileNotFoundError(
        "Could not find Instacart data. Expected files under data/raw/instacart/ or data/raw/."
    )


def ensure_output_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def load_orders(data_dir: Path) -> pd.DataFrame:
    log("Loading orders metadata...")
    return pd.read_csv(
        data_dir / "orders.csv",
        usecols=[
            "order_id",
            "user_id",
            "eval_set",
            "order_number",
            "order_dow",
            "order_hour_of_day",
            "days_since_prior_order",
        ],
        dtype={
            "order_id": "int32",
            "user_id": "int32",
            "eval_set": "category",
            "order_number": "int16",
            "order_dow": "int8",
            "order_hour_of_day": "int8",
            "days_since_prior_order": "float32",
        },
    )


def load_prior_products(data_dir: Path) -> pd.DataFrame:
    log("Loading prior order-product rows...")
    return pd.read_csv(
        data_dir / "order_products__prior.csv",
        usecols=["order_id", "product_id", "add_to_cart_order", "reordered"],
        dtype={
            "order_id": "int32",
            "product_id": "int32",
            "add_to_cart_order": "int16",
            "reordered": "int8",
        },
    )


def load_products(data_dir: Path) -> pd.DataFrame:
    log("Loading product catalog...")
    return pd.read_csv(
        data_dir / "products.csv",
        usecols=["product_id", "product_name", "aisle_id", "department_id"],
        dtype={
            "product_id": "int32",
            "product_name": "string",
            "aisle_id": "int16",
            "department_id": "int16",
        },
    )


def select_users(prior_orders: pd.DataFrame) -> pd.DataFrame:
    log("Selecting users with enough prior-order history...")
    prior_order_counts = (
        prior_orders.groupby("user_id")["order_id"].count().rename("prior_order_count")
    )
    eligible_users = prior_order_counts[prior_order_counts >= MIN_PRIOR_ORDERS]
    selected_users = eligible_users.sort_values(ascending=False).head(TARGET_USERS)
    return selected_users.reset_index()


def build_baskets(
    prior_orders: pd.DataFrame, prior: pd.DataFrame, products: pd.DataFrame, selected_user_ids: set[int]
) -> pd.DataFrame:
    sample_orders = prior_orders[prior_orders["user_id"].isin(selected_user_ids)].copy()
    sample_order_ids = set(sample_orders["order_id"].tolist())

    log(f"Building baskets for {len(selected_user_ids):,} sampled users...")
    sample_prior = prior[prior["order_id"].isin(sample_order_ids)].copy()
    sample_merged = sample_prior.merge(sample_orders, on="order_id", how="inner")
    sample_merged = sample_merged.merge(products, on="product_id", how="left")
    sample_merged = sample_merged.sort_values(["user_id", "order_number", "add_to_cart_order"])

    baskets = (
        sample_merged.groupby("order_id")
        .agg(
            user_id=("user_id", "first"),
            order_number=("order_number", "first"),
            order_dow=("order_dow", "first"),
            order_hour_of_day=("order_hour_of_day", "first"),
            days_since_prior_order=("days_since_prior_order", "first"),
            basket_size=("product_id", "size"),
            reordered_items=("reordered", "sum"),
            product_ids=("product_id", list),
            product_names=("product_name", lambda x: x.astype(str).tolist()),
            aisle_ids=("aisle_id", lambda x: sorted(set(x.dropna().astype(int).tolist()))),
            department_ids=(
                "department_id",
                lambda x: sorted(set(x.dropna().astype(int).tolist())),
            ),
        )
        .reset_index()
    )

    baskets["unique_aisle_count"] = baskets["aisle_ids"].apply(len)
    baskets["unique_department_count"] = baskets["department_ids"].apply(len)
    baskets["reorder_ratio"] = baskets["reordered_items"] / baskets["basket_size"]
    baskets = baskets.sort_values(["user_id", "order_number"]).reset_index(drop=True)
    return baskets


def build_hidden_item_examples(baskets: pd.DataFrame) -> pd.DataFrame:
    log("Creating hidden-item examples from later orders in each user history...")
    eligible = baskets[(baskets["basket_size"] >= 3) & (baskets["order_number"] >= 2)].copy()

    eligible["target_product_id"] = eligible["product_ids"].apply(lambda items: items[-1])
    eligible["target_product_name"] = eligible["product_names"].apply(lambda items: items[-1])
    eligible["context_product_ids"] = eligible["product_ids"].apply(lambda items: items[:-1])
    eligible["context_product_names"] = eligible["product_names"].apply(lambda items: items[:-1])
    eligible["context_size"] = eligible["context_product_ids"].apply(len)

    return eligible[
        [
            "order_id",
            "user_id",
            "order_number",
            "order_dow",
            "order_hour_of_day",
            "days_since_prior_order",
            "basket_size",
            "context_size",
            "unique_aisle_count",
            "unique_department_count",
            "reorder_ratio",
            "context_product_ids",
            "context_product_names",
            "target_product_id",
            "target_product_name",
        ]
    ].copy()


def write_outputs(
    baskets: pd.DataFrame, examples: pd.DataFrame, selected_users: pd.DataFrame
) -> None:
    output_dir = ensure_output_dir()
    baskets_output = output_dir / "instacart_user_history_baskets.csv"
    examples_output = output_dir / "instacart_user_history_examples.csv"
    summary_output = output_dir / "instacart_user_history_summary.json"

    log(f"Writing baskets to {baskets_output}...")
    baskets.to_csv(baskets_output, index=False)
    log(f"Writing hidden-item examples to {examples_output}...")
    examples.to_csv(examples_output, index=False)

    summary = {
        "sampled_users": int(len(selected_users)),
        "min_prior_orders": MIN_PRIOR_ORDERS,
        "total_baskets": int(len(baskets)),
        "eligible_hidden_item_examples": int(len(examples)),
        "average_prior_orders_per_user": round(float(selected_users["prior_order_count"].mean()), 2),
        "median_prior_orders_per_user": round(float(selected_users["prior_order_count"].median()), 2),
        "average_basket_size": round(float(baskets["basket_size"].mean()), 2),
        "median_basket_size": round(float(baskets["basket_size"].median()), 2),
    }
    summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote user-history baskets to: {baskets_output}")
    print(f"Wrote user-history examples to: {examples_output}")
    print(f"Wrote summary to: {summary_output}")
    print(json.dumps(summary, indent=2))


def main() -> int:
    try:
        data_dir = resolve_data_dir()
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    orders = load_orders(data_dir)
    prior_orders = orders[orders["eval_set"] == "prior"].copy()
    prior = load_prior_products(data_dir)
    products = load_products(data_dir)

    selected_users = select_users(prior_orders)
    selected_user_ids = set(selected_users["user_id"].tolist())

    baskets = build_baskets(prior_orders, prior, products, selected_user_ids)
    examples = build_hidden_item_examples(baskets)
    write_outputs(baskets, examples, selected_users)
    return 0


if __name__ == "__main__":
    sys.exit(main())
