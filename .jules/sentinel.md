## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## YYYY-MM-DD - Fix XSS bypass in sanitizeUrl
**Vulnerability:** The sanitizeUrl function could be bypassed by inserting control characters or whitespace into malicious protocols (e.g., \x01javascript:), leading to DOM-based XSS.
**Learning:** Browsers ignore certain control characters in URLs, but simple regex matching on the protocol string without stripping these characters will fail to detect the malicious protocol.
**Prevention:** Always strip control characters and whitespace from a URL string before validating its protocol against a blocklist, while preserving the original string for benign URLs.
