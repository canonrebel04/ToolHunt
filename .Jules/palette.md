## 2026-05-27 - ARIA Live Regions for Dynamic Search
**Learning:** Dynamic search results updated via AJAX need `aria-live="polite"` to notify screen readers without forcing focus changes. Adding `aria-atomic="true"` ensures the entire count string is read instead of just the changed number.
**Action:** Always check dynamically updated text elements (like result counts or status messages) to ensure they have appropriate ARIA live attributes.
