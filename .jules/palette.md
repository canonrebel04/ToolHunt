## 2024-08-26 - Keyboard Accessibility Trap on Disabled Links
**Learning:** Using `pointer-events: none` on links with `href="#"` does not prevent keyboard interactions (like tabbing and Enter) from triggering the link or scrolling the page.
**Action:** Always conditionally render the `href` attribute and add `tabindex="-1"` along with `aria-disabled="true"` for disabled link elements.
