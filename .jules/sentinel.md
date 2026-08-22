## 2023-10-27 - Flask Secret Key Configuration
**Vulnerability:** Application could start in production with a `None` or weak default `dev` SECRET_KEY if the environment variable was missing.
**Learning:** Checking configuration at the class level (e.g. `ProductionConfig`) causes module-level import errors that break local testing and auto-reloading.
**Prevention:** Always enforce production-only critical configuration constraints inside the Flask application factory (e.g. `create_app`) *after* configs are fully loaded, using `if app.debug is False and app.config.get('TESTING') is False:`.
