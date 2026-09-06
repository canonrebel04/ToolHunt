## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
