## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Improved Disabled Link Accessibility]
**Learning:** When disabling anchor tags, using `pointer-events: none` suppresses hover events, preventing tooltips from showing and breaking accessibility.
**Action:** Use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` while providing a `title` attribute to ensure the disabled state is clear and accessible without losing hover context.
