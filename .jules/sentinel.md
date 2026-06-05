## 2024-06-05 - Hardcoded Secret Key in Production Config
**Vulnerability:** Found a hardcoded `SECRET_KEY` ('change-this-in-production') in the `ProductionConfig` class in `app/config.py`.
**Learning:** Having placeholder secrets directly in the source code can easily be deployed to production if not overridden, leading to complete session hijacking and forgery capabilities since Flask uses the secret key to sign session cookies.
**Prevention:** Always use environment variables (`os.environ.get('SECRET_KEY')`) for production configurations. Do not provide a default value for production, forcing the deployment process to explicitly provide the key.
