## 2024-06-17 - Hardcoded Production Secret Key
**Vulnerability:** The Flask application's `ProductionConfig` in `app/config.py` contained a hardcoded placeholder `SECRET_KEY = 'change-this-in-production'`. If left unchanged during deployment, this would allow attackers to forge session cookies and potentially execute arbitrary code.
**Learning:** Configurations intended for production often contain obvious placeholder strings instead of enforcing secure environment variable injection, leading to insecure defaults if the deployment process overlooks updating them.
**Prevention:** Always use `os.environ.get('SECRET_KEY')` or similar environment-based mechanisms for production configuration values, ensuring that sensitive data is injected at runtime and not stored in source control.
