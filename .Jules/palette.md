## 2026-07-01 - Add keyboard accessibility for disabled links
**Learning:** Visually disabled links (using `pointer-events: none`) are still keyboard accessible and will appear in the tab order unless `tabindex="-1"` is added. They will also be announced as normal links by screen readers unless `aria-disabled="true"` is also used.
**Action:** Always include `tabindex="-1"` and `aria-disabled="true"` alongside `pointer-events: none` when creating pseudo-disabled anchor tags to ensure a consistent experience across mouse, keyboard, and screen reader users.
