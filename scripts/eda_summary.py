from __future__ import annotations

from pathlib import Path

import pandas as pd


EXPECTED_FILES = {
    "orders.csv",
    "order_products__prior.csv",
    "products.csv",
    "aisles.csv",
    "departments.csv",
}


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


def main() -> None:
    data_dir = resolve_data_dir()

    orders = pd.read_csv(data_dir / "orders.csv")
    prior = pd.read_csv(data_dir / "order_products__prior.csv")
    products = pd.read_csv(data_dir / "products.csv")
    aisles = pd.read_csv(data_dir / "aisles.csv")
    departments = pd.read_csv(data_dir / "departments.csv")

    prior_with_products = prior.merge(products, on="product_id", how="left")
    basket_sizes = prior.groupby("order_id")["product_id"].count()
    top_products = (
        prior_with_products["product_name"].value_counts().head(10).rename_axis("product_name")
    )
    top_aisles = (
        prior_with_products.merge(aisles, on="aisle_id", how="left")["aisle"]
        .value_counts()
        .head(10)
        .rename_axis("aisle")
    )
    top_departments = (
        prior_with_products.merge(departments, on="department_id", how="left")["department"]
        .value_counts()
        .head(10)
        .rename_axis("department")
    )

    print("Instacart EDA summary")
    print(f"Data directory: {data_dir}")
    print(f"Users: {orders['user_id'].nunique():,}")
    print(f"Orders: {orders['order_id'].nunique():,}")
    print(f"Prior baskets: {prior['order_id'].nunique():,}")
    print(f"Products: {products['product_id'].nunique():,}")
    print(f"Average basket size: {basket_sizes.mean():.2f}")
    print(f"Median basket size: {basket_sizes.median():.2f}")
    print(f"Orders with 3+ items: {(basket_sizes >= 3).sum():,}")

    print("\nTop products:")
    for product_name, count in top_products.items():
        print(f"- {product_name}: {count:,}")

    print("\nTop aisles:")
    for aisle, count in top_aisles.items():
        print(f"- {aisle}: {count:,}")

    print("\nTop departments:")
    for department, count in top_departments.items():
        print(f"- {department}: {count:,}")


if __name__ == "__main__":
    main()
