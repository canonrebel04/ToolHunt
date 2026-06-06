## 2024-03-22 - Conditional ARIA Labels in Dynamic HTML
**Learning:** When dynamically generating HTML elements that use `aria-label`, ensure the label string is conditionally formatted to match any conditional visual text logic (e.g., 'Access Tool' vs 'No Link Available'). Static aria-labels override visual text and can cause major accessibility regressions if they do not reflect the dynamic state.
**Action:** Always map dynamic visual state changes directly to their corresponding ARIA attributes during component generation.
