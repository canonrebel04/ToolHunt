## 2024-08-01 - Interactive Divs Require Manual Accessibility
**Learning:** Custom interactive elements built with `<div>` (like fallback category tiles) completely lack native accessibility features, meaning keyboard users cannot activate them or see focus states.
**Action:** Always add `role="button"`, `tabindex="0"`, explicit `:focus-visible` styles, and keyboard event handlers (for Enter and Space keys) when converting non-semantic elements into interactive controls.
