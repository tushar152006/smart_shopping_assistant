# EDA Plan

## Goal

Understand the Instacart dataset well enough to design a reliable forgotten-item pipeline.

## Questions To Answer

1. How many users, orders, and products are in the dataset?
2. What is the average basket size?
3. Which products are most frequent overall?
4. Which products are most frequently reordered?
5. Which product pairs appear together most often?
6. How many baskets are suitable for hidden-item training examples?
7. How skewed is the product popularity distribution?
8. Which aisles and departments dominate the data?

## First Visuals To Create

- Basket size histogram
- Top 20 products bar chart
- Top 20 aisles bar chart
- Reorder-rate distribution
- Co-purchase heatmap for top products

## Checks Before Modeling

- Missing-value scan
- Duplicate row scan
- Product metadata join completeness
- User order sequence consistency
- Basket-size filter impact

## EDA Deliverables

- Dataset summary table
- Key plots saved for documentation
- Notes on leakage risks
- Feature candidates for modeling

