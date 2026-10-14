## 2026-08-31 - Keyboard Interaction Interception Patterns
**Learning:** Implementing a global keydown listener (like '/') can unintentionally trap users inside standard inputs or textareas, completely breaking their ability to type. Optional chaining and activeElement type checking is critical to avoid stealing focus away from expected typing activities.
**Action:** When adding global keyboard shortcuts to complex UIs, explicitly verify the `tagName` of the `document.activeElement` and ignore events propagating from form inputs to preserve baseline accessibility.

## 2026-10-14 - Screen Reader Context for External Links
**Learning:** When using target="_blank" for external links, visual users see a new tab open, but screen reader users lose context entirely. Using a visually-hidden span like `<span class="visually-hidden">(opens in a new tab)</span>` preserves this critical navigation context for non-visual users.
**Action:** Always append visually hidden text to indicate external link behavior, and pair it with rel="noopener noreferrer" for security.
