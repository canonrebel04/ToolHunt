## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Improved Disabled Link Accessibility]
**Learning:** Using `pointer-events: none` on disabled elements suppresses hover events and makes them inaccessible to screen readers. We should always use `cursor: not-allowed` along with `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` to ensure disabled states are both visually and semantically accessible.
**Action:** When disabling anchor tags or other interactive elements, replace `pointer-events: none` with proper accessible attributes (`aria-disabled`, `tabindex`) and JS event prevention, ensuring tooltips and semantic states remain intact for all users.
