## 2024-07-22 - Missing focus indicators for keyboard navigation
**Learning:** Found that most interactive elements like buttons and links (`.search-box button`, `.example-tag`, `.tool-link`, `.load-more`) do not have clear `:focus-visible` styles, impacting keyboard navigation accessibility.
**Action:** Always verify keyboard accessibility and add `:focus-visible` pseudo-class with clear focus rings to interactive elements, rather than just relying on hover states.
