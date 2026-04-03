from __future__ import annotations

from pathlib import Path
import json

import pandas as pd


EXPECTED_FILES = {
    "orders.csv",
    "order_products__prior.csv",
    "products.csv",
}
SAMPLE_SIZE = 10_000


def resolve_data_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    candidates = [root / "data" / "raw" / "instacart", root / "data" / "raw"]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            existing = {path.name for path in candidate.iterdir() if path.is_file()}
            if EXPECTED_FILES.issubset(existing):
                return candidate
    raise FileNotFoundError(
        "Could not find Instacart data. Expected files under data/raw/instacart/ or data/raw/."
    )


def ensure_output_dir() -> Path:
    root = Path(__file__).resolve().parents[1]
    output_dir = root / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def log(message: str) -> None:
    print(f"[build_training_examples] {message}", flush=True)


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


def compute_summary(prior: pd.DataFrame) -> tuple[pd.Series, dict[str, int | float]]:
    log("Computing full-dataset basket statistics...")
    basket_sizes = prior.groupby("order_id")["product_id"].size()
    summary = {
        "total_baskets": int(len(basket_sizes)),
        "eligible_hidden_item_examples": int((basket_sizes >= 3).sum()),
        "average_basket_size": round(float(basket_sizes.mean()), 2),
        "median_basket_size": round(float(basket_sizes.median()), 2),
        "sample_size": SAMPLE_SIZE,
    }
    return basket_sizes, summary


def build_basket_details(
    prior: pd.DataFrame,
    prior_orders: pd.DataFrame,
    products: pd.DataFrame,
    target_order_ids: list[int],
) -> pd.DataFrame:
    log(f"Building detailed basket records for {len(target_order_ids):,} sampled orders...")
    sample_prior = prior[prior["order_id"].isin(target_order_ids)].copy()
    sample_orders = prior_orders[prior_orders["order_id"].isin(target_order_ids)].copy()

    sample_merged = sample_prior.merge(sample_orders, on="order_id", how="inner")
    sample_merged = sample_merged.merge(products, on="product_id", how="left")
    sample_merged = sample_merged.sort_values(["order_id", "add_to_cart_order"])

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

    return baskets


def build_hidden_item_examples(baskets: pd.DataFrame) -> pd.DataFrame:
    eligible = baskets[baskets["basket_size"] >= 3].copy()

    # Simple deterministic target choice for the first baseline:
    # hide the final added item to simulate a missing product.
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


def build_outputs() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int | float]]:
    data_dir = resolve_data_dir()
    orders = load_orders(data_dir)
    prior_orders = orders[orders["eval_set"] == "prior"].copy()
    prior = load_prior_products(data_dir)
    products = load_products(data_dir)

    basket_sizes, summary = compute_summary(prior)
    basket_sample_ids = basket_sizes.head(SAMPLE_SIZE).index.tolist()
    eligible_sample_ids = basket_sizes[basket_sizes >= 3].head(SAMPLE_SIZE).index.tolist()
    sampled_order_ids = sorted(set(basket_sample_ids) | set(eligible_sample_ids))

    baskets = build_basket_details(prior, prior_orders, products, sampled_order_ids)
    baskets = baskets.sort_values("order_id").reset_index(drop=True)
    examples = build_hidden_item_examples(
        baskets[baskets["order_id"].isin(eligible_sample_ids)].copy()
    )
    basket_sample = baskets[baskets["order_id"].isin(basket_sample_ids)].copy()
    basket_sample = basket_sample.head(SAMPLE_SIZE).reset_index(drop=True)
    example_sample = examples.head(SAMPLE_SIZE).reset_index(drop=True)

    return basket_sample, example_sample, summary


def write_outputs(
    baskets: pd.DataFrame, examples: pd.DataFrame, summary: dict[str, int | float]
) -> None:
    output_dir = ensure_output_dir()

    baskets_output = output_dir / "instacart_baskets_sample.csv"
    examples_output = output_dir / "instacart_hidden_item_examples_sample.csv"
    summary_output = output_dir / "instacart_summary.json"

    log(f"Writing basket sample to {baskets_output}...")
    baskets.to_csv(baskets_output, index=False)
    log(f"Writing hidden-item example sample to {examples_output}...")
    examples.to_csv(examples_output, index=False)
    summary_output.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Wrote basket sample to: {baskets_output}")
    print(f"Wrote hidden-item example sample to: {examples_output}")
    print(f"Wrote summary to: {summary_output}")
    print(json.dumps(summary, indent=2))


def main() -> None:
    baskets, examples, summary = build_outputs()
    write_outputs(baskets, examples, summary)


if __name__ == "__main__":
    main()
