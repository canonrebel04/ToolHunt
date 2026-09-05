## 2023-10-27 - Enforce Secret Key in Production
**Vulnerability:** Missing validation for SECRET_KEY in production config allowed the app to run with a None secret key.
**Learning:** Relying on os.environ.get() without a fallback or validation check can lead to missing crucial secrets in production.
**Prevention:** Always validate critical environment variables and raise explicit errors during initialization if they are missing.

## YYYY-MM-DD - Fix DOM XSS in tool display
**Vulnerability:** DOM-based XSS vulnerability via innerHTML interpolation.
**Learning:** Direct interpolation of data into innerHTML without escaping allows script execution if data is manipulated.
**Prevention:** Always sanitize data using HTML escaping before injecting it into innerHTML, and validate URLs for malicious protocols.
