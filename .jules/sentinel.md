## $(date +%Y-%m-%d) - Fix hardcoded secret key in config
**Vulnerability:** A hardcoded `SECRET_KEY = 'change-this-in-production'` was found in the `ProductionConfig` class in `app/config.py`.
**Learning:** Default boilerplate configurations or placeholder strings can accidentally be deployed into production, exposing the application to session hijacking or signature forging.
**Prevention:** Always use environment variables (e.g., `os.environ.get('SECRET_KEY')`) for sensitive keys, especially in production configuration classes, to enforce external management of secrets.
