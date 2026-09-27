## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Improved Disabled Link Accessibility]
**Learning:** Using `pointer-events: none` on disabled links completely suppresses hover events, making tooltips unavailable and reducing accessibility for screen readers.
**Action:** Use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` instead to ensure disabled states are semantically clear and remain accessible.
