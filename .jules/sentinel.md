## 2026-08-26 - Enforce Secure Configuration in Flask Factory
**Vulnerability:** Application could silently start in production using insecure default configurations (like a hardcoded 'dev' SECRET_KEY) if environment variables were missing.
**Learning:** Enforcing configuration constraints (like SECRET_KEY validation) should occur within the application factory (`create_app()`) after the configuration object is loaded, rather than in the configuration class body, which evaluates at import time and disrupts testing/local dev.
**Prevention:** Implement explicit runtime checks (e.g., `app.debug is False and app.config.get('TESTING') is False`) within the factory to assert production invariants before initialization completes.
