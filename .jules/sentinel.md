## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## YYYY-MM-DD - Fix XSS protocol sanitization bypass via control characters
**Vulnerability:** The `sanitizeUrl` function used `.trim()` before checking for malicious protocols. This allowed XSS filter bypasses via embedded control characters like tab or newline (e.g., `java\tscript:`).
**Learning:** Whitespace stripping must remove all control characters throughout the string to correctly defend against protocol-based XSS vectors.
**Prevention:** Always strip all control characters and whitespaces using regex like `replace(/[\x00-\x20]/g, '')` before validating URIs.
