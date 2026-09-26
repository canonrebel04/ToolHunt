## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Disabled Anchor Links]
**Learning:** pointer-events: none is bad for accessibility because it suppresses hover events, preventing tooltips or screen reader interactions.
**Action:** Always use cursor: not-allowed, aria-disabled='true', tabindex='-1', and prevent navigation with onclick='return false;' for disabled anchor links.
