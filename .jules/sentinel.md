## 2024-05-18 - Hardcoded Production Secrets
**Vulnerability:** A hardcoded `SECRET_KEY` was found in `ProductionConfig` in `app/config.py`.
**Learning:** Hardcoded secrets in production configurations can lead to unauthorized access and security breaches if the codebase is exposed or compromised.
**Prevention:** Always use environment variables or a secure secrets management system for sensitive configuration values like `SECRET_KEY` in production environments.
