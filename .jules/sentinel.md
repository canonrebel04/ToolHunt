## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## 2024-03-22 - Fix URL protocol sanitization bypass
**Vulnerability:** The URL sanitizer `sanitizeUrl` failed to detect malicious protocols (like `javascript:`) if they contained whitespace or control characters (e.g., `java\tscript:`), allowing XSS.
**Learning:** Browsers ignore whitespace and control characters in URLs, but basic regex protocol checks do not. This mismatch creates a sanitization bypass.
**Prevention:** Always strip all whitespace and control characters (`[\x00-\x20]`) from URLs before validating their protocols against blocklists.
