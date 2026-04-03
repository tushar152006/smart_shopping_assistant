# Phase 1 EDA Findings

## Dataset Health Check

The Instacart dataset validated successfully in the local workspace.

## Baseline Facts

Observed from the first summary run:

- Users: 206,209
- Orders: 3,421,083
- Prior baskets: 3,214,874
- Products: 49,688
- Average basket size: 10.09
- Median basket size: 8
- Baskets with at least 3 items: 2,871,133

## Early Insights

- The dataset is large enough for meaningful recommendation experiments.
- The hidden-item framing is practical because there are millions of baskets with at least 3 products.
- Produce and dairy dominate the product mix, so popularity bias will matter.
- Very common products like bananas may inflate naive metrics, so we should report more than one evaluation metric.

## Modeling Implications

Recommended first metrics:

- Recall@K
- Precision@K
- Hit Rate@K
- Coverage

Recommended first baselines:

- Global popularity baseline
- Basket co-occurrence baseline
- Association-rule baseline

## Next Engineering Step

Build processed basket examples from raw Instacart data so Phase 2 can start with repeatable inputs.

