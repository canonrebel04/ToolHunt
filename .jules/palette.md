## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Accessible Disabled Links]
**Learning:** Using `pointer-events: none` on disabled anchor tags prevents tooltips and hover events from working, making the disabled state less clear to users.
**Action:** Always use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` instead of `pointer-events: none` to disable links while preserving hover capabilities.
