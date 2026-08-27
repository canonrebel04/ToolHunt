## 2025-02-24 - Keyboard Focus on Disabled Links
**Learning:** Using `pointer-events: none` on an `<a>` tag with an `href` does not prevent it from receiving keyboard focus. Keyboard users can still tab to the link and activate it, causing unexpected page jumps.
**Action:** When conditionally disabling links, conditionally omit the `href` attribute and add `tabindex="-1"` along with `aria-disabled="true"` to fully remove it from the keyboard navigation flow and properly communicate its state to screen readers.
