# AGENTS.md — Smart Shopping Assistant Guidelines

This document provides mandatory operational instructions for AI coding agents working in this repository.

---

## 1. Frontend & UI Engineering Standards (Mandatory)

Whenever creating, modifying, refactoring, or reviewing any frontend code (HTML, CSS, React, components, layouts):

You **MUST** activate and strictly enforce the guidelines from the 4 installed workspace skills in `.agents/skills/`:

1. **`frontend-design`** (`.agents/skills/frontend-design/`):
   - **Grounded Aesthetic**: Establish a distinctive grocery/retail identity (crisp emerald greens `#0F5132` / `#198754`, warm organic neutrals `#F8F9FA` / `#FAF6F0`, high-contrast slate text, warm amber rule badges).
   - **Typography**: Use intentional typography scales (e.g. Plus Jakarta Sans or Outfit with Inter). Never use generic browser unstyled fallbacks or plain Arial.
   - **No Clichés**: Do NOT use generic AI templates (e.g., standard purple-to-blue gradients, plain centered card walls, or floating neon blur blobs).

2. **`impeccable`** (`.agents/skills/impeccable/`):
   - **Visual Hierarchy & Whitespace**: Ensure deliberate spatial rhythm (4px/8px grid scale), clear visual contrast, and high information density.
   - **Self-Critique & Polish**: Audit every component for layout stability, tactile click feedback, and balanced margins before declaring completion.

3. **`motion-design`** (`.agents/skills/motion-design/`):
   - **Intentional Timing**: Micro-interactions must use calibrated durations (150ms–250ms for buttons/badges, 300ms for basket additions/removals).
   - **Directional Easing**: Use ease-out for entrances, ease-in for exits, and responsive spring physics for item interactions.
   - **Accessibility**: Always respect `prefers-reduced-motion` media queries.

4. **`web-design-guidelines`** (`.agents/skills/web-design-guidelines/`):
   - **Semantic HTML**: Use `<button>` for actions, `<a>` for links. Never `<div onClick>`.
   - **Accessible Focus**: Always provide visible `:focus-visible` focus rings (never `outline: none` without a high-contrast replacement).
   - **Touch Targets**: Minimum 44×44px interactive targets for buttons and icons.
   - **Tabular Figures**: Use `font-variant-numeric: tabular-nums` for prediction scores, order numbers, and quantities to prevent Cumulative Layout Shift (CLS).
   - **Live Updates**: Prediction updates and async fetching states must use `aria-live="polite"`.

---

## 2. Machine Learning & Backend Architecture

1. **FastAPI Endpoints**: Keep the service modular and stateless where possible; leverage pre-built serialized artifacts in `backend/artifacts/` (`predictor.pkl`, `products_catalog.json`) for sub-15ms response latencies.
2. **Explainability**: Every forgotten-item prediction MUST include human-interpretable rationale (e.g. historical frequency, co-occurrence rules, or recency signals).
3. **Test Integrity**: Run pytest suite (`pytest -v`) after changes to ensure all unit and integration tests continue to pass.
