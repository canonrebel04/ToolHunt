
## 2024-05-24 - [Enforce Production SECRET_KEY]
**Vulnerability:** The Flask application lacked an explicit check to prevent starting in production mode with a weak or default `SECRET_KEY` ('dev').
**Learning:** Default fallback strings (like 'dev') in configuration classes can silently propagate to production if not explicitly overridden by environment variables, potentially compromising session security.
**Prevention:** Always implement application-level assertions in the application factory (after loading configurations) to hard-fail if production-critical secrets remain at their default values.
