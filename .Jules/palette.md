## 2026-08-31 - Keyboard Interaction Interception Patterns
**Learning:** Implementing a global keydown listener (like '/') can unintentionally trap users inside standard inputs or textareas, completely breaking their ability to type. Optional chaining and activeElement type checking is critical to avoid stealing focus away from expected typing activities.
**Action:** When adding global keyboard shortcuts to complex UIs, explicitly verify the `tagName` of the `document.activeElement` and ignore events propagating from form inputs to preserve baseline accessibility.
