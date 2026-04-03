# Phase 1 Foundation

## Objective

Turn the project idea into a buildable engineering target.

## Phase 1 Output

By the end of this phase, we should have:

- A clear MVP definition
- A chosen dataset
- A planned folder structure
- A list of model inputs and outputs
- A local development setup plan

## MVP Definition

Version 1 should do only this:

1. Accept a basket of current items
2. Predict likely forgotten items
3. Show a short reason for each suggestion

Version 1 should not require:

- User authentication
- Production deployment
- Paid APIs
- Complex orchestration tools

## Recommended Dataset

Primary choice:

- Instacart Market Basket Analysis

Why:

- Well-known structure
- Order history is suitable for basket analysis
- Good for association patterns and interpretable modeling

Backup choices:

- RetailRocket
- Dunnhumby

## Initial Folder Plan

```text
smart_shopping_assistat/
  README.md
  docs/
    PROJECT_ROADMAP.md
    PHASE_1_FOUNDATION.md
  data/
    raw/
    processed/
  notebooks/
  backend/
  frontend/
  models/
  scripts/
  tests/
```

## Core ML Problem Framing

Suggested framing:

- Input: current basket plus optional historical purchase signals
- Output: ranked list of likely forgotten items

Possible training strategy:

- For each user's order sequence, use previous orders and partial current basket context
- Predict items that are commonly present but missing from the current basket

## Baseline Modeling Order

Build in this order:

1. Frequency baseline
2. Association-rule baseline
3. Decision-tree or rule-list model
4. Optional black-box comparison model

This order keeps the project explainable and easier to debug.

## Explanation Strategy

Start with deterministic templates such as:

- "You often buy X with Y."
- "People who buy A and B often also buy C."
- "This item appears frequently in similar baskets."

Only add an LLM when:

- We already have good predictions
- We already have trustworthy rule evidence
- We want more natural language polish

## Risks To Avoid Early

- Building auth too soon
- Choosing too many datasets
- Using paid APIs before the baseline works
- Mixing research experiments with app code too early

## Immediate Next Tasks

1. Create the actual project folders
2. Add `.gitignore`
3. Define the dataset ingestion plan
4. Start the EDA notebook
5. Write the data schema document

## Phase 1 Status

- [x] Project folders created
- [x] `.gitignore` added
- [x] Dataset choice recommended
- [x] MVP scope defined
- [ ] Dataset setup completed locally
- [ ] Raw files placed in `data/raw/instacart/`
- [ ] EDA notebook started
- [ ] First preprocessing script implemented

## Phase 1 Working Documents

- `docs/DATASET_SETUP.md`
- `docs/DATA_SCHEMA.md`
- `notebooks/01_eda_plan.md`
- `requirements.txt`
