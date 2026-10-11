## 2026-08-31 - Keyboard Interaction Interception Patterns
**Learning:** Implementing a global keydown listener (like '/') can unintentionally trap users inside standard inputs or textareas, completely breaking their ability to type. Optional chaining and activeElement type checking is critical to avoid stealing focus away from expected typing activities.
**Action:** When adding global keyboard shortcuts to complex UIs, explicitly verify the `tagName` of the `document.activeElement` and ignore events propagating from form inputs to preserve baseline accessibility.

## YYYY-MM-DD - Disabled Link Accessibility
**Learning:** Using `pointer-events: none` on links visually disables hover effects but fails to provide the 'not-allowed' cursor context and hides the state from screen readers. It prevents necessary keyboard interactions without proper aria labels.
**Action:** Always replace `pointer-events: none` on interactive elements with `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and explicitly prevent default actions (e.g., `onclick="return false;"`) to ensure full accessibility.
