## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Accessible Disabled Anchor Tags]
**Learning:** Suppressing interactions on disabled anchor tags with `pointer-events: none` is an accessibility anti-pattern because it suppresses hover events, preventing tooltips from appearing. Additionally, `.textContent` correctly ignores icon elements, so slicing the text can inadvertently truncate valid multi-word input.
**Action:** Always use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` for disabled links while providing a tooltip to explain the disabled state.
## 2026-10-12 - [Accessible Alerts and Pagination Button States]
**Learning:** Found that alert messages lacked ARIA roles, preventing screen readers from automatically announcing them, and that the pagination 'Load More' button lacked a disabled/loading state during async operations, risking redundant API calls.
**Action:** Always add `role="alert"` and `aria-live="assertive"` to dynamically created alert messages, and implement `disabled` state with visual opacity and a loading spinner for pagination buttons during async fetches.
