## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Accessible Disabled Links]
**Learning:** When disabling anchor tags (<a>) while preserving tooltips, do not use pointer-events: none as it suppresses hover events.
**Action:** Use cursor: not-allowed, add aria-disabled="true" and tabindex="-1", and explicitly prevent navigation with onclick="return false;".
