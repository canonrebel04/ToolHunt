## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Improved Disabled Link Accessibility]
**Learning:** Using `pointer-events: none` on disabled anchor tags prevents tooltip hover events from triggering, harming accessibility.
**Action:** When disabling anchor tags (<a>), use `cursor: not-allowed`, add `aria-disabled="true"` and `tabindex="-1"`, and explicitly prevent navigation with `onclick="return false;"` while preserving tooltip functionality (e.g., using a `title` attribute).
