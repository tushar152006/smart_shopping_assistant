# PRODUCT.md — Smart Shopping Assistant

## Overview
Smart Shopping Assistant is an AI-powered retail assistant engineered to prevent the "forgotten-item problem" in grocery shopping. Instead of opaque black-box recommendations, it uses interpretable machine learning (historical user purchase frequency, recency signals, and co-occurrence association rules) to predict what users may have forgotten, paired with human-readable explanations.

## Primary User & Job to be Done
- **Shopper Persona**: Busy household grocery buyers and repeat shoppers creating their weekly order.
- **Job**: Add items to their virtual cart and receive intelligent, real-time reminders for essential items they commonly purchase or that pair with their current selections, preventing second trips or missed ingredients.

## Core Differentiating Mechanism
1. **Explainability First**: Every suggestion clearly states *why* it was suggested (e.g. *"You purchased this in 14 previous orders"*, or *"Frequently bought together with Whole Milk and Organic Bananas"*).
2. **Personalized Context**: Combines collective association rules with individual purchase recency bonuses.
3. **Sub-15ms Local Serving**: Lightweight serialized predictor served via FastAPI.

## Platform & Architecture
- **Platform**: Web (Desktop & Mobile responsive)
- **Frontend**: React + Vite
- **Styling**: Modern Vanilla CSS with design tokens (zero heavy framework overhead, high custom animation control)
- **Backend**: FastAPI with serialized machine learning artifacts (`predictor.pkl`, `products_catalog.json`)
- **Primary Layout**: Live Split-View (Interactive Cart & Product Search on the left, Real-Time Forgotten Item Suggestions & Explanations on the right)

## Success Criteria
- Sub-50ms round-trip prediction updates when basket changes.
- Accessible keyboard navigation and zero layout shift (CLS).
- High-contrast, transparent explanation cards for each suggested item.
