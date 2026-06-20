## 2024-05-15 - Hardcoded Production Secret Key
**Vulnerability:** A hardcoded `SECRET_KEY` was found in `ProductionConfig` (`app/config.py`).
**Learning:** Development defaults ('change-this-in-production') were committed directly to code, posing a severe risk if deployed without proper environment configuration, allowing attackers to forge session cookies or CSRF tokens.
**Prevention:** Always use environment variables (e.g. `os.environ.get('SECRET_KEY')`) for sensitive secrets in production configurations to ensure credentials are injected securely at runtime and not stored in version control.
