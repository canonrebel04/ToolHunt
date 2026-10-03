## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.

## YYYY-MM-DD - [Preserve Tooltips and Keyboard Accessibility on Disabled Links]
**Learning:** Using `pointer-events: none` on disabled links (like <a> tags) suppresses hover events, preventing tooltips from showing and breaking keyboard navigability.
**Action:** Use `cursor: not-allowed` along with `aria-disabled="true"`, `tabindex="-1"`, and explicitly prevent navigation (e.g., `onclick="return false;"`) to maintain accessibility while indicating a disabled state.
