## 2026-06-04 - Focus visibility and Dynamic ARIA labels
**Learning:** Default browser focus rings are often invisible against dark backgrounds. Dynamically generated text like 'Access Tool' needs dynamically formatted aria-labels so screen readers get full context.
**Action:** Always add explicit :focus-visible rules for dark themes, and ensure dynamically rendered links with ambiguous text get context-aware aria-labels.
