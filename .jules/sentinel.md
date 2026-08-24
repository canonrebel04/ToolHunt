## 2024-08-24 - Enforce SECRET_KEY in Application Factory
**Vulnerability:** Hardcoded Flask SECRET_KEY in base configuration could be unintentionally used in production.
**Learning:** Raising exceptions directly inside the Config class body disrupts module import and test discovery. The validation must occur in the application factory (create_app) after the configuration is fully loaded.
**Prevention:** Use a static, non-production fallback string in Config, and validate it in create_app() by checking app.debug and app.config.get('TESTING').
