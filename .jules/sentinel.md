## 2024-08-05 - Hardcoded Secrets in Config
**Vulnerability:** Hardcoded SECRET_KEY in ProductionConfig.
**Learning:** Hardcoded overrides in derived config classes can lead to accidental exposure of secrets in production environments.
**Prevention:** Use environment variables in the base Config class with a static, non-production fallback, and remove overrides in derived classes to ensure secure, dynamic inheritance.
