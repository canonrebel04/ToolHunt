## YYYY-MM-DD - Dynamic Search Accessibility
**Learning:** Dynamic DOM updates for search results are not automatically announced to screen readers, causing a disconnected UX for visually impaired users. Using `aria-live="polite"` on the results count and `role="status"` on the loading indicator ensures state changes are gracefully announced without interrupting the user's typing.
**Action:** Always wrap dynamic count updates and loading states in `aria-live` regions when implementing asynchronous search features.
