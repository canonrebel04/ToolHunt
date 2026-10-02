## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Improved Disabled Anchor Links Accessibility]
**Learning:** Found that using pointer-events: none on disabled anchor links suppresses tooltip/hover events, breaking accessibility. Purely decorative FontAwesome icons also lacked aria-hidden attributes.
**Action:** Use cursor: not-allowed, aria-disabled="true", tabindex="-1", and onclick="return false;" instead of pointer-events for disabled links to allow tooltips. Always apply aria-hidden="true" to decorative icons.
