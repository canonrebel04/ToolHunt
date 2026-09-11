## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Accessible Disabled Links]
**Learning:** Using pointer-events: none on disabled links suppresses hover events (and tooltips) and hurts accessibility.
**Action:** Use cursor: not-allowed, aria-disabled="true", tabindex="-1", and prevent navigation with onclick="return false;".
