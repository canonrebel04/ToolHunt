## 2024-06-04 - Hardcoded Secret Key in Production Configuration
**Vulnerability:** A hardcoded `SECRET_KEY = 'change-this-in-production'` was found in the `ProductionConfig` within `app/config.py`.
**Learning:** Hardcoded credentials or placeholder secrets in version control pose a severe security risk, as they might be deployed accidentally or leaked, compromising the application's session management and encryption. The codebase should default to failing securely or reading from environment variables dynamically.
**Prevention:** Always use environment variables or secure secret managers (e.g., `os.environ.get('SECRET_KEY')`) for sensitive configuration values. Never commit secrets, even placeholders, directly into the source code.
