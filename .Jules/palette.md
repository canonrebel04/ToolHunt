## 2024-06-18 - Keyboard Accessibility Focus Styles
**Learning:** Default browser focus rings are often completely invisible against dark, cyberpunk-themed backgrounds (`#111111` or `#0a0a0a`), breaking keyboard accessibility for elements like inputs, selects, and buttons.
**Action:** Always verify keyboard accessibility on dark-themed apps and ensure interactive elements have explicit `*:focus-visible` styles utilizing existing design tokens (e.g., `--primary`) to ensure adequate contrast.
