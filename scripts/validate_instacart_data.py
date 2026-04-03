from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


EXPECTED_FILES = {
    "orders.csv",
    "order_products__prior.csv",
    "order_products__train.csv",
    "products.csv",
    "aisles.csv",
    "departments.csv",
}

REQUIRED_COLUMNS = {
    "orders.csv": {"order_id", "user_id", "eval_set", "order_number"},
    "order_products__prior.csv": {"order_id", "product_id", "add_to_cart_order"},
    "order_products__train.csv": {"order_id", "product_id", "add_to_cart_order"},
    "products.csv": {"product_id", "product_name", "aisle_id", "department_id"},
    "aisles.csv": {"aisle_id", "aisle"},
    "departments.csv": {"department_id", "department"},
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


def validate_files(data_dir: Path) -> list[str]:
    issues: list[str] = []

    for filename in sorted(EXPECTED_FILES):
        path = data_dir / filename
        if not path.exists():
            issues.append(f"Missing file: {filename}")
            continue

        df = pd.read_csv(path, nrows=5)
        missing_columns = REQUIRED_COLUMNS[filename] - set(df.columns)
        if missing_columns:
            issues.append(
                f"{filename} is missing required columns: {', '.join(sorted(missing_columns))}"
            )

    return issues


def summarize(data_dir: Path) -> None:
    orders = pd.read_csv(data_dir / "orders.csv")
    prior = pd.read_csv(data_dir / "order_products__prior.csv")
    products = pd.read_csv(data_dir / "products.csv")

    print(f"Resolved data directory: {data_dir}")
    print(f"Orders rows: {len(orders):,}")
    print(f"Prior order-product rows: {len(prior):,}")
    print(f"Products rows: {len(products):,}")
    print(f"Unique users: {orders['user_id'].nunique():,}")
    print(f"Unique orders: {orders['order_id'].nunique():,}")
    print(f"Unique products: {products['product_id'].nunique():,}")


def main() -> int:
    try:
        data_dir = resolve_data_dir()
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    issues = validate_files(data_dir)
    if issues:
        print("Validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Instacart dataset validation passed.")
    summarize(data_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

