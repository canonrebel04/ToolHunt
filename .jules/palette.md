## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Preserved Tooltips on Disabled Links]
**Learning:** Using `pointer-events: none` on disabled anchor links suppresses hover events, preventing tooltips or title attributes from appearing, which hurts accessibility and discoverability.
**Action:** Use `cursor: not-allowed`, add `aria-disabled="true"`, `tabindex="-1"`, and explicitly prevent navigation with `onclick="return false;"` to disable links while maintaining hover interactions.
