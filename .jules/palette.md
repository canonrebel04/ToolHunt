## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Improved Disabled Link Accessibility]
**Learning:** Found that using `pointer-events: none` on disabled anchor tags (`<a>`) incorrectly suppresses mouse hover events (preventing custom cursors) and is opaque to screen readers.
**Action:** When disabling links, instead of `pointer-events: none`, use `cursor: not-allowed`, add `aria-disabled="true"`, `tabindex="-1"` to block keyboard focus, and explicitly prevent navigation with `onclick="return false;"` to maintain full accessibility and provide clear visual feedback.
