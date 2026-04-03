# Data Schema

## Purpose

This document defines the core entities and model-facing tables for the MVP.

## Raw Entities

### `orders`

Main source: `orders.csv`

Important fields:

- `order_id`: unique order identifier
- `user_id`: unique user identifier
- `eval_set`: one of `prior`, `train`, `test`
- `order_number`: order index for a user
- `order_dow`: day of week
- `order_hour_of_day`: hour of day
- `days_since_prior_order`: recency signal

### `order_products_prior`

Main source: `order_products__prior.csv`

Important fields:

- `order_id`
- `product_id`
- `add_to_cart_order`
- `reordered`

### `order_products_train`

Main source: `order_products__train.csv`

Important fields:

- `order_id`
- `product_id`
- `add_to_cart_order`
- `reordered`

### `products`

Main source: `products.csv`

Important fields:

- `product_id`
- `product_name`
- `aisle_id`
- `department_id`

### `aisles`

Main source: `aisles.csv`

Important fields:

- `aisle_id`
- `aisle`

### `departments`

Main source: `departments.csv`

Important fields:

- `department_id`
- `department`

## MVP Analytical Entities

### Basket

A basket is the set of products within one order.

Proposed basket representation:

- `order_id`
- `user_id`
- `basket_items`: list of product IDs
- `basket_size`
- `order_number`
- `order_timestamp_features`

### Candidate Suggestion

A candidate suggestion is a product that may be missing from the current basket.

Proposed fields:

- `user_id`
- `order_id`
- `candidate_product_id`
- `candidate_score`
- `evidence_type`
- `evidence_value`

### Explanation Record

The explanation record connects a suggestion to an interpretable reason.

Proposed fields:

- `candidate_product_id`
- `explanation_template`
- `supporting_products`
- `confidence_score`
- `rule_id`

## Modeling Target Definition

We should start with a practical target:

- Given a partially observed basket, predict items that are likely to appear in the completed basket but are currently missing.

## Training Example Strategy

Recommended first strategy:

1. Build full baskets from order history.
2. For each basket, hide one item from baskets of size at least 3.
3. Use the remaining items as input.
4. Treat the hidden item as the target label.

Why this works:

- It simulates forgotten-item prediction
- It is simple to implement
- It supports ranking evaluation

## Initial Feature Set

### Basket-Level Features

- basket size
- unique aisle count
- unique department count
- hour of day
- day of week

### User-Product Features

- product purchase frequency for a user
- reorder rate
- recency since last purchase
- number of prior purchases

### Co-Occurrence Features

- pairwise co-purchase count
- confidence from association rules
- support from association rules
- lift from association rules

## Output Contract For MVP Predictor

The backend predictor should eventually return:

```json
{
  "basket_items": [24852, 13176],
  "predictions": [
    {
      "product_id": 21137,
      "product_name": "Organic Strawberries",
      "score": 0.81,
      "reason": "Users often buy this with bananas and milk."
    }
  ]
}
```

## Phase 1 Decisions Locked In

- Primary dataset: Instacart
- MVP target: hidden-item recovery from partial baskets
- First explanation style: rule-based templates
- First baseline: frequency plus association rules

