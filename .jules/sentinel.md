## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## 2024-03-12 - Fix DOM-based XSS bypasses and error sinks
**Vulnerability:** URL sanitization bypassed via control characters, and error messages injected unescaped into innerHTML.
**Learning:** URL sanitizers must strip whitespace/control characters before regex matching. Error messages must always be escaped before being rendered via innerHTML.
**Prevention:** Always use robust sanitization stripping all non-printable characters for URLs and escape all dynamic content going into innerHTML.
