
## 2024-06-19 - Adding Focus Styles for Keyboard Accessibility
**Learning:** Default browser focus rings are often invisible against dark backgrounds, failing keyboard accessibility. Physical shape properties like border-radius should be excluded from global focus styles to prevent overriding specific component shapes.
**Action:** Implemented a global *:focus-visible style with high-contrast outlines and offsets to maintain keyboard accessibility across all interactive elements.
