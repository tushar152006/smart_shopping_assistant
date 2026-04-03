# Smart Shopping Assistant Roadmap

## Vision

Build a trustworthy shopping assistant that predicts likely forgotten items and explains those suggestions in a simple, human-friendly way.

## Why This Version Of The Plan

The original plan is strong, but to build this carefully and affordably we should separate:

1. The research goal
2. The MVP product goal
3. The optional advanced AI integrations

That keeps us from getting blocked by datasets, paid APIs, or deployment complexity too early.

## Recommended Build Order

### Phase 0: Project Setup And Scope Lock

Goal:
Define exactly what version 1 must do.

Deliverables:

- Finalized problem statement
- MVP scope
- Repository structure
- Initial backlog
- Success metrics for MVP

Exit criteria:

- We agree on one dataset path
- We agree on one backend stack
- We agree on one explanation approach for MVP

### Phase 1: Research And Dataset Foundation

Goal:
Understand the forgotten-item problem and prepare a usable dataset.

Deliverables:

- Research summary
- Dataset choice and download instructions
- Data dictionary
- Initial EDA checklist

Exit criteria:

- Dataset is selected
- Core entities are defined: user, order, item, basket, target label
- We know how we will create training examples

### Phase 2: Data Pipeline And Baselines

Goal:
Create clean, repeatable preprocessing and a baseline forgotten-item signal.

Deliverables:

- Data cleaning pipeline
- Train/validation/test split
- Basic association-rule baseline
- Baseline metrics

Exit criteria:

- We can run preprocessing from raw data to model-ready features
- We have at least one working baseline predictor

### Phase 3: Interpretable Predictor

Goal:
Train models that are useful and explainable.

Deliverables:

- Feature engineering pipeline
- Decision-tree or rule-based model
- Evaluation notebook
- Exported rules

Exit criteria:

- Top-K recommendation quality is measurable
- Model behavior is understandable by humans
- We can explain why an item was suggested

### Phase 4: Explanation Layer

Goal:
Turn model output into user-facing explanations.

Recommended order:

1. Template-based explanations
2. Optional LLM explanations only after templates work well

Deliverables:

- Explanation generator module
- Prompt or template library
- Fallback strategy

Exit criteria:

- Every prediction can produce a readable explanation
- The app still works without a paid API

### Phase 5: Backend API

Goal:
Expose prediction and explanation features through a stable API.

Deliverables:

- FastAPI app
- Prediction endpoint
- Explanation endpoint
- Health checks
- Basic tests

Exit criteria:

- Frontend can call the backend locally
- Core flows work without manual notebook steps

### Phase 6: Frontend MVP

Goal:
Build a simple but polished web experience.

Deliverables:

- Basket editor
- Suggested forgotten items panel
- Explanation display
- Basic history view

Exit criteria:

- A user can enter items and receive suggestions with explanations
- The interface works on desktop and mobile

### Phase 7: Integration, Reliability, And Deployment

Goal:
Make the system demo-ready and stable.

Deliverables:

- End-to-end integration
- Error handling
- Logging
- Deployment setup

Exit criteria:

- We can demo the full flow reliably
- The app is deployed or ready to deploy

### Phase 8: Research Packaging And Evaluation

Goal:
Turn the implementation into a research-quality artifact.

Deliverables:

- Evaluation report
- Ablation results
- Demo assets
- Paper draft

Exit criteria:

- Results are reproducible
- Research narrative matches the implemented system

## MVP Scope Recommendation

For the first complete version, build only this:

- User enters a basket
- System predicts 1-3 likely forgotten items
- System shows a short explanation
- No full auth system yet
- No multi-user production deployment yet

This is the fastest path to something real and testable.

## Architecture Recommendation

### MVP

- React frontend
- FastAPI backend
- SQLite database
- Local model artifacts
- Rule/template explanations

### Later Upgrades

- PostgreSQL
- Real user accounts
- LLM-based explanation upgrade
- Advanced experimentation tracking

## Free-First Tool Recommendations

These are the best options for now:

- Dataset work: Kaggle datasets locally
- ML experiments: Jupyter notebooks plus Python scripts
- Backend: FastAPI
- Frontend: React + Vite
- Styling: Tailwind
- Database: SQLite first
- Deployment: Vercel for frontend

## Current External Tool Notes

Based on official sources checked on April 3, 2026:

- Vercel has a free Hobby plan for personal projects: https://vercel.com/docs/accounts/plans
- Supabase documents a Free plan, which can be useful later if we want hosted auth and database services: https://supabase.com/docs/guides/platform/aws-marketplace/manage-your-subscription

Inference from those sources:

- Vercel is a good frontend deployment choice for MVP
- Supabase is better as an optional later upgrade, not a day-one dependency

## Recommended Decisions For This Project

I recommend we commit to the following unless a later constraint forces a change:

1. Use Instacart as the primary dataset for the first version
2. Start with interpretable rules plus decision trees
3. Use template explanations before adding any LLM
4. Build the local MVP before thinking about full deployment
5. Treat the research paper as a later packaging step, not the first build step

## What We Should Build Next

The next step is Phase 1:

1. Create the final project structure
2. Lock the MVP scope
3. Define the dataset schema and preprocessing targets
4. Start the research summary and dataset setup docs

