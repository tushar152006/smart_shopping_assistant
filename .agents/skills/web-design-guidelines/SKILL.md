---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines and accessibility compliance. Use when designing, reviewing, or polishing web components to ensure production-grade accessibility (WCAG 2.2 AA), focus management, layout stability, and performance.
---

# Web Interface Guidelines & Accessibility Standards

Review and build all UI components against these rigorous interface guidelines.

## 1. Accessibility & Semantics (WCAG 2.2 AA)

- **Semantic Elements First**: Use `<button>` for actions, `<a>` for navigation. Never `<div onClick>`.
- **Icon Buttons**: Icon-only buttons MUST have an explicit `aria-label`.
- **Form Controls**: All inputs must have associated `<label>` (via `htmlFor` or wrapping) or `aria-label`.
- **Images & Icons**: Meaningful images require descriptive `alt`; decorative icons must have `aria-hidden="true"`.
- **Live Regions**: Asynchronous state updates (alerts, error messages, real-time predictions) must use `aria-live="polite"`.
- **Touch Targets**: All interactive elements must meet the minimum 44x44px touch target requirement.
- **Hierarchy**: Maintain strict heading hierarchy (`<h1>` through `<h6>`).

## 2. Focus States & Keyboard Navigation

- **Visible Focus**: Interactive elements MUST have visible focus rings: `focus-visible:ring-2` or equivalent CSS.
- **Never Outline None**: Never use `outline: none` without an immediate high-contrast `:focus-visible` replacement.
- **Click vs Keyboard**: Use `:focus-visible` rather than `:focus` so mouse clicks don't show focus rings.
- **Compound Controls**: Use `:focus-within` for combined inputs and search bars.

## 3. Forms & Inputs

- **Autocomplete & Types**: Inputs must have appropriate `type` (`text`, `search`, `number`) and `name`.
- **Never Block Paste**: Never prevent pasting on inputs.
- **Immediate Feedback**: Submit buttons stay enabled until request starts; show subtle spinner/loading state during network latency.
- **Inline Errors**: Display error messages adjacent to the erroneous field.

## 4. Typography & Numbers

- **Tabular Numbers**: Use `font-variant-numeric: tabular-nums` for price columns, quantity badges, and score metrics to prevent layout shifts.
- **Widow Prevention**: Apply `text-wrap: balance` or `text-wrap: pretty` on headers and card titles.
- **Punctuation**: Use proper ellipsis `…` instead of `...` for loading states (e.g., `"Predicting items…"`).

## 5. Performance & Layout Stability

- **Zero Cumulative Layout Shift (CLS)**: Pre-allocate space for dynamic content, badges, and prediction cards with min-heights or skeleton placeholders.
- **Flexbox Truncation**: Children of flex containers with truncating text must have `min-w-0` to avoid horizontal layout breaking.
- **Clean Transitions**: Animate `transform` and `opacity` only (compositor-friendly GPU layers). Never use `transition: all`.
- **Reduced Motion**: Respect `prefers-reduced-motion` media queries for all animations.
