## 2024-05-14 - Conditionally Formatting ARIA Labels
**Learning:** When dynamically generating HTML elements with varying visual states (e.g., active vs. disabled links with different inner text like "Access Tool" vs "No Link Available"), screen readers will read incorrect states if an unconditional `aria-label` overrides the text.
**Action:** Always conditionally format `aria-label` strings to match any conditional visual text logic so the screen reader context accurately reflects the visual UI.
