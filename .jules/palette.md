## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Improved Disabled Links Accessibility]
**Learning:** Using `pointer-events: none` on disabled anchor tags prevents tooltips from displaying on hover, hindering accessibility and user understanding of the disabled state.
**Action:** Use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` instead of `pointer-events: none` to disable anchor tags while preserving hover events for tooltips.
