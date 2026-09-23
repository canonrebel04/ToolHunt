## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## YYYY-MM-DD - Fix XSS bypass in protocol sanitization
**Vulnerability:** The `sanitizeUrl` function in frontend was vulnerable to bypasses using control characters (e.g., `java	script:`).
**Learning:** Basic regex matching against protocol strings fails if control characters or whitespaces are ignored. Sanitization requires stripping all such characters before regex validation.
**Prevention:** Strip all control characters (`[\x00-\x20]`) from URLs prior to checking for dangerous protocols.
