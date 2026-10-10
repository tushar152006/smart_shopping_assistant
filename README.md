# Smart Shopping Assistant 🛒
**Explainable Forgotten-Item Prediction Engine for Online Grocery Shoppers**

[![CI Pipeline](https://github.com/tushar152006/smart_shopping_assistant/actions/workflows/ci.yml/badge.svg)](https://github.com/tushar152006/smart_shopping_assistant/actions)
[![Live Demo](https://img.shields.io/badge/Demo-Vercel%20Live-10b981?style=flat&logo=vercel)](https://smart-shopping-assistant-zeta.vercel.app)
[![API Status](https://img.shields.io/badge/API-Render%20Live-0ea5e9?style=flat&logo=render)](https://smart-shopping-assistant-35m7.onrender.com/api/health)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-3776ab?style=flat&logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-19-61dafb?style=flat&logo=react)](https://react.dev/)

---

## 🌟 Live Deployments

- **Web Application (Vercel)**: [https://smart-shopping-assistant-zeta.vercel.app](https://smart-shopping-assistant-zeta.vercel.app)
- **API Engine (Render)**: [https://smart-shopping-assistant-35m7.onrender.com](https://smart-shopping-assistant-35m7.onrender.com)
- **Interactive Swagger Docs**: [https://smart-shopping-assistant-35m7.onrender.com/docs](https://smart-shopping-assistant-35m7.onrender.com/docs)

---

## 💡 Overview

Online grocery shoppers frequently forget essential staples (milk, bananas, olive oil) when finalizing their carts. Traditional recommender systems optimize for impulse purchases or click-through rates rather than **basket completeness**.

**Smart Shopping Assistant** solves this by combining:
1. **Association Rule Mining & Multi-Item Co-occurrence**: Learning staple relationships across Instacart shopping baskets.
2. **Personalized Purchase Frequency & Recency**: Factoring in individual shopper reorder cycles and past favorites.
3. **Transparent Explainability**: Every recommendation is accompanied by human-interpretable rationale explaining *why* the item was flagged.
4. **Sub-15ms Latency**: Pre-computed, serialized feature artifacts served by an asynchronous FastAPI backend.

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────┐
│               React 19 + Vite Frontend                 │
│         (Hosted on Vercel · 72 kB gzip bundle)         │
│  - Instant Autocomplete across 16,344 catalog products │
│  - Real-time forgotten item radar                      │
│  - Shopper persona switcher & 1-click cart management  │
└──────────────────────────┬─────────────────────────────┘
                           │ HTTPS / JSON API
┌──────────────────────────▼─────────────────────────────┐
│                 FastAPI REST Backend                   │
│        (Hosted on Render · Containerized Docker)       │
│  - GET  /api/health            (Container diagnostics) │
│  - GET  /api/products/search   (Substring autocomplete)│
│  - GET  /api/users/sample      (Persona history)       │
│  - POST /api/predict           (Explainable inference) │
└──────────────────────────┬─────────────────────────────┘
                           │ In-Memory Fast Lookup
┌──────────────────────────▼─────────────────────────────┐
│              Machine Learning Artifacts                │
│  - predictor.pkl          (Serialized hybrid model)    │
│  - products_catalog.json  (16,344 catalog entries)     │
│  - sample_users.json      (Shopper order profiles)     │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Features

- **Personalized & Guest Modes**: Switch seamlessly between guest basket analysis (pure co-occurrence) and 20 real historical shopper personas.
- **Explainable Rationale**: Cards show clear explanations (e.g., *"Purchased in 100% of past orders"*, *"Strong association with Bananas and Milk"*).
- **Hardened Security**:
  - OWASP defensive HTTP headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`).
  - Strict Pydantic input boundary limits against DoS attacks.
  - Non-root unprivileged Docker container user (`appuser`).
  - Zero sensitive secrets or credentials in source.

---

## 🧪 Local Development & Testing

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/tushar152006/smart_shopping_assistant.git
cd smart_shopping_assistant

# Install Python dependencies
pip install -r requirements.txt

# Run full test suite
pytest -v

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Run linter
npm run lint

# Start Vite dev server
npm run dev
```

---

## 📜 License
MIT License. Built for portfolio & production use.
