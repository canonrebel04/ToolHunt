## 2026-08-29 - DOM-based XSS via innerHTML
**Vulnerability:** XSS vulnerability found in frontend where backend database results were unsafely injected into DOM via innerHTML.
**Learning:** Relying purely on backend sanitization (or no sanitization for database values) leaves the frontend vulnerable to Stored XSS if DB is compromised.
**Prevention:** Always escape HTML entities before injecting data into the DOM using innerHTML or use textContent.
