# DESIGN.md — Smart Shopping Assistant Design System

## Aesthetic Identity: Artisan Grocery & Intelligent Retail
The interface reflects a fresh, trustworthy grocery identity rather than a generic SaaS dashboard. It pairs natural organic earth tones with crisp emerald accents, tactile card layouts, and transparent explanation callouts.

---

## 1. Color Palette Tokens

```css
:root {
  /* Brand Primary */
  --color-primary-900: #0B3D26;
  --color-primary-800: #0F5132;
  --color-primary-600: #198754;
  --color-primary-500: #22C55E;
  --color-primary-100: #DCFCE7;
  --color-primary-50: #F0FDF4;

  /* Surfaces & Neutrals */
  --color-bg-canvas: #FAF8F5;
  --color-bg-surface: #FFFFFF;
  --color-bg-panel: #F3EFEA;
  --color-border: #E5DFD7;
  --color-border-subtle: #F0ECE6;

  /* Typography */
  --color-text-main: #141A17;
  --color-text-secondary: #4A5568;
  --color-text-muted: #718096;

  /* Accents & Status */
  --color-amber-bg: #FEF3C7;
  --color-amber-text: #92400E;
  --color-amber-border: #FDE68A;
  --color-blue-bg: #EFF6FF;
  --color-blue-text: #1E40AF;
  --color-danger-bg: #FEE2E2;
  --color-danger-text: #991B1B;
}
```

---

## 2. Typography Hierarchy

- **Headings Font**: `'Plus Jakarta Sans', system-ui, sans-serif`
  - Hero `h1`: 32px / 1.2 / 800 weight / letter-spacing: -0.02em
  - Section `h2`: 22px / 1.3 / 700 weight / letter-spacing: -0.015em
  - Card `h3`: 16px / 1.4 / 600 weight
- **Body Font**: `'Inter', system-ui, sans-serif`
  - Body standard: 14px / 1.5 / 400 weight
  - Small labels & chips: 12px / 1.4 / 500 weight
  - Numerals: `font-variant-numeric: tabular-nums` for all scores, counts, and prices.

---

## 3. Spatial Rhythm & Layout

- **Scale**: Multiples of 4px / 8px (4, 8, 12, 16, 24, 32, 48px).
- **Split-View Canvas**:
  - **Left Panel (Cart & Search)**: 55% width on desktop, flexible card grid.
  - **Right Panel (Predictive Radar & Explanations)**: 45% width on desktop, persistent sticky feed.
- **Card Styling**: 1px subtle organic border (`var(--color-border)`), 12px border radius, soft multi-layer shadow (`0 2px 8px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.02)`).

---

## 4. Motion Design & Micro-Interactions

- **Button Click / Hover**: `150ms cubic-bezier(0.2, 0, 0, 1)` scale(0.98) on active.
- **Item Add to Cart**: `250ms cubic-bezier(0.16, 1, 0.3, 1)` spring-like pop and slide down.
- **Prediction Pill Pulse**: Subtle 2s pulse on high confidence score badge (> 0.85).
- **Reduced Motion**: Gracefully falls back to simple opacity transitions when `prefers-reduced-motion` is active.

---

## 5. Accessibility & Touch Standards

- Visible `:focus-visible` ring: `outline: 2px solid var(--color-primary-600); outline-offset: 2px`.
- Minimum 44×44px interactive tap area on mobile and touch devices.
- `aria-live="polite"` on prediction change container for screen reader accessibility.
