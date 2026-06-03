## 2024-06-03 - Dynamic ARIA Labels in Template Literals
**Learning:** When conditionally rendering link text (like 'Access Tool' vs 'No Link Available'), static ARIA labels will override the visual text and mislead screen reader users. The aria-label must dynamically match the conditional state.
**Action:** Always test conditionally rendered UI elements to ensure their aria-labels accurately reflect the rendered state.
