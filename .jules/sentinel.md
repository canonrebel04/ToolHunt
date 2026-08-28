## 2026-08-28 - Flask Production Config Constraint
**Vulnerability:** A Flask application factory did not enforce that a strong SECRET_KEY was set in production.
**Learning:** Enforcing production-only configuration constraints should be done within the application factory (after config load and avoiding `config_class.__name__`) to avoid raising exceptions during import, local development, or testing.
**Prevention:** In Flask, evaluate both `app.debug` and `app.config.get('TESTING')` to identify production environments and validate critical settings there.
