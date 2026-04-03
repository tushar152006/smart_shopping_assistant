# Dataset Setup

## Primary Dataset

We will use the Instacart Market Basket Analysis dataset for the first version of the project.

Expected raw files:

- `orders.csv`
- `order_products__prior.csv`
- `order_products__train.csv`
- `products.csv`
- `aisles.csv`
- `departments.csv`

## Expected Folder Layout

Preferred layout:

```text
data/
  raw/
    instacart/
      orders.csv
      order_products__prior.csv
      order_products__train.csv
      products.csv
      aisles.csv
      departments.csv
```

Also supported:

```text
data/
  raw/
    orders.csv
    order_products__prior.csv
    order_products__train.csv
    products.csv
    aisles.csv
    departments.csv
```

## Manual Download Steps

1. Create or sign in to your Kaggle account.
2. Open the Instacart Market Basket Analysis competition page.
3. Accept the competition rules if required.
4. Download the dataset files.
5. Extract them into `data/raw/instacart/` or directly into `data/raw/`.

Reference:

- https://www.kaggle.com/c/instacart-market-basket-analysis

## Raw Data Notes

Key files:

- `orders.csv`: order metadata and split information
- `order_products__prior.csv`: products in historical orders
- `order_products__train.csv`: products in train orders
- `products.csv`: product metadata
- `aisles.csv`: aisle names
- `departments.csv`: department names

## Recommended Local Environment

Python version:

- Python 3.11 is a good default

Recommended environment setup:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Data Validation Checklist

Before we write preprocessing code, verify:

- All expected CSV files exist
- File names match exactly
- CSV files can be opened without corruption
- `orders.csv` contains `eval_set`
- `order_products__prior.csv` contains `order_id` and `product_id`
- `products.csv` contains `product_name`

## What I May Need From You

You can help by doing one of these:

- Download the Instacart dataset and place it in `data/raw/instacart/`
- Tell me if you want to use a different dataset instead

If you place the files in either supported layout, I can immediately build the ingestion and EDA pipeline next.

