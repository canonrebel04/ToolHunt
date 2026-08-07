## 2025-09-04 - [Hardcoded Secret Key in Flask Config]
**Vulnerability:** A hardcoded `SECRET_KEY = 'dev'` was found in the base `Config` class in `app/config.py`. Although `ProductionConfig` attempts to override it with `os.environ.get('SECRET_KEY')`, the fallback isn't explicitly handled securely. Furthermore, we need to enforce that the secret key is actually set in production.
**Learning:** Hardcoded default secrets can be accidentally deployed if environments aren't properly distinguished or if `os.environ.get` returns `None` and falls back to a default empty/weak string in certain configurations.
**Prevention:** Use `os.environ.get('SECRET_KEY', 'default-dev-key')` only for development. For production, enforce that it's strictly set and not missing.
