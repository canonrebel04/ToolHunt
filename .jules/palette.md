## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Accessible Disabled Links]
**Learning:** When disabling anchor tags, `pointer-events: none` suppresses all mouse events (including hover for tooltips). Furthermore, anchor tags without `href` or with dummy `href` still remain focusable if not handled correctly.
**Action:** Use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` to provide visual feedback, prevent keyboard focus, stop navigation securely, and allow hover tooltips.
