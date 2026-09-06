## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.

## 2024-03-21 - Fix DOM XSS in Tool Rendering
**Vulnerability:** User-controlled data (tool name, description, link) was unsafely injected directly into innerHTML in static/js/app.js.
**Learning:** Template literals combined with innerHTML are a prime target for DOM-based XSS if variables aren't escaped. Protocol sanitization alone for URLs (stripping javascript:) is insufficient if attribute-breakouts aren't also mitigated.
**Prevention:** Always use safe DOM manipulation methods (like textContent) or strictly enforce HTML-escaping and protocol validation functions before interpolating variables into innerHTML.
