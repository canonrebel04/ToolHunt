## YYYY-MM-DD - Disabled links keyboard focus
**Learning:** Using 'pointer-events: none' on disabled links prevents mouse clicks but leaves them in the keyboard focus order (tabbing), confusing screen reader and keyboard users.
**Action:** Add 'tabindex="-1"' and 'aria-disabled="true"' to effectively remove disabled links from the accessibility tree and focus order.
