## 2026-08-27 - Prevent Hardcoded Fallback Secrets
**Vulnerability:** Found a hardcoded 'dev' fallback string for SECRET_KEY in the Config class which could leak into production if the environment variable is missed.
**Learning:** Relying on defaults in base configuration classes is risky since subclasses like ProductionConfig inherit them unless explicitly overwritten.
**Prevention:** Use os.environ.get with the default in the base Config, but strictly validate the presence and validity of the secret key in the application factory (create_app) for production environments, raising an error if absent.
