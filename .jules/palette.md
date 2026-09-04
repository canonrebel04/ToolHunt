
## YYYY-MM-DD - Link Keyboard Accessibility
**Learning:** Applying `pointer-events: none` on anchor tags visually disables them but does not prevent keyboard navigation, creating a trap for screen reader/keyboard users. Disabled links must also use `tabindex="-1"` and `aria-disabled="true"`.
**Action:** Always ensure visually disabled interactive elements are fully removed from the focus order and semantically marked as disabled.
