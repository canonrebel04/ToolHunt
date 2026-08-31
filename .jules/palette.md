## 2026-08-19 - Keyboard Trap in Disabled Links
**Learning:** Using 'pointer-events: none' on an <a> tag with href='#' creates a keyboard trap because the element remains focusable via the tab key but cannot be interacted with, frustrating screen reader and keyboard users.
**Action:** Use a semantically appropriate element like a <span> with aria-disabled='true' when a link action is unavailable.
