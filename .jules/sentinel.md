## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## YYYY-MM-DD - [Protocol Sanitization Bypass via Control Characters]
**Vulnerability:** The sanitizeUrl function in the frontend could be bypassed using control characters or whitespace (e.g., java\tscript:) which evaded the regex test but would still execute in the browser.
**Learning:** Simple .trim() is insufficient for URL sanitization because browsers ignore whitespace and control characters in attributes, allowing them to bypass simple prefix regex checks.
**Prevention:** Strip all control characters and whitespace (using replace(/[\x00-\x20]/g, '')) before performing regex testing for dangerous protocols like javascript:.
