## Sentinel Journal
## 2025-05-24 - Hardcoded Secret Key in Flask Configuration
**Vulnerability:** Found a hardcoded `SECRET_KEY` in the `ProductionConfig` class in `app/config.py`.
**Learning:** Hardcoding secrets like Flask's `SECRET_KEY` in version control can lead to session hijacking and cryptographic signing bypass if an attacker gains read access to the source code.
**Prevention:** Always use environment variables (e.g., `os.environ.get('SECRET_KEY')`) for sensitive configuration values in production environments.
