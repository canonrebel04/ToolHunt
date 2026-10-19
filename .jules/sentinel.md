## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.
## YYYY-MM-DD - Fix DOM-based XSS in frontend app
**Vulnerability:** User input values (tool name, description, link) were injected directly into innerHTML in static/js/app.js, exposing the app to DOM-based XSS and attribute breakout attacks.
**Learning:** When injecting dynamic content into the DOM using innerHTML, developers must sanitize text context and HTML attributes. Protocol stripping alone is insufficient for anchor hrefs.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers for link attributes.
## YYYY-MM-DD - Fix XSS vulnerabilities in frontend error handlers
**Vulnerability:** Error messages containing user-controlled input were injected directly into innerHTML without sanitization, and URL protocol sanitizer was bypassable with control characters.
**Learning:** When injecting dynamic content into the DOM using innerHTML (even in error handlers like showAlert or showError), developers must sanitize text context. Protocol stripping alone is insufficient if control characters aren't stripped first.
**Prevention:** Always HTML-escape variables injected into templates and combine it with specific protocol sanitizers that strip control characters first.
## 2026-10-12 - [Sanitization Normalization Order Bypass]
**Vulnerability:** XSS bypass caused by applying normalization (`.trim()`) before stripping control characters in URL sanitization.
**Learning:** Unicode spaces (like `\xa0`) survive `.trim()` and can bypass protocol regex checks (like `javascript:`) if control characters are stripped *after* trimming. The final stripped string executes as a script but evades the regex.
**Prevention:** Always normalize (`.trim()`) inputs *after* stripping invalid or control characters to ensure the resulting string cannot conceal malicious payloads.
## 2026-10-13 - Rate Limiter Memory Leak (DoS)
**Vulnerability:** The RateLimiter cached requests but never invoked its `cleanup()` method, causing an unbounded memory leak when tracking requests from numerous unique IPs.
**Learning:** In-memory caches or rate limiters that store state per-client must have an active eviction strategy or periodically purge stale entries to prevent Denial of Service (DoS) via memory exhaustion.
**Prevention:** Always verify that cleanup routines are actually invoked, either asynchronously or lazily during regular request processing, when implementing custom in-memory caching mechanisms.
## 2025-05-18 - X-Forwarded-For Rate Limiting Spoofing
**Vulnerability:** The rate limiter blindly trusted the `request.remote_addr` without applying `ProxyFix`, meaning behind a proxy all requests share the proxy's IP. A naive fix of manually parsing `X-Forwarded-For` and trusting the leftmost IP introduces an IP spoofing bypass.
**Learning:** In Flask/Werkzeug applications running behind reverse proxies (like Docker/Gunicorn), manually parsing proxy headers is strongly discouraged and insecure. An attacker can append a fake IP to the `X-Forwarded-For` header.
**Prevention:** Always use `werkzeug.middleware.proxy_fix.ProxyFix` and configure it with exactly the number of trusted upstream proxies (e.g., `x_for=1`) to securely handle proxy headers.
