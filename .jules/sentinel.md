## 2024-10-27 - Enforce SECURE_KEY in Production Environment
**Vulnerability:** Application could be deployed to production with a missing or default `SECRET_KEY`, leading to session forging vulnerabilities.
**Learning:** Checking for production configurations in the Flask application factory is tricky if class configurations are evaluated directly since they run at import time. Thus, the check must be placed within `create_app` after `config` is fully loaded, specifically asserting that the environment isn't debugging or testing.
**Prevention:** Always place dynamic fallback or environmental assertions within the application factory to ensure accurate context (like `app.debug` and `app.config['TESTING']`) before deciding the safety of security configurations.
