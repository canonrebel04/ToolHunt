## 2025-06-07 - Add explicit focus-visible styles for keyboard navigation in dark themes
**Learning:** Default browser focus rings are often invisible against dark backgrounds or overridden globally. Interactive elements must have explicit `:focus-visible` styles (e.g., a bright outline) to maintain keyboard navigation accessibility.
**Action:** Always add a global `:focus-visible` rule with a high-contrast outline color for dark themes, and override it selectively if specific elements (like inputs) already have custom focus states (e.g., box-shadow).
