## 2023-10-25 - Interactive Element Accessibility
**Learning:** `pointer-events: none` on anchor tags disables mouse clicks but still allows keyboard focus and Enter key activation (which navigates to `#` and jumps the page). Additionally, using `div` for clickable fallback tiles entirely prevents keyboard navigation.
**Action:** Always use native `<button>` elements for clickable cards, and explicitly remove `href` (using `tabindex="-1" aria-disabled="true"`) on disabled links to ensure a robust keyboard and screen-reader flow.
