## 2024-08-15 - Missing Production SECRET_KEY Validation in Flask Factory
**Vulnerability:** The Flask application could start in a production environment with a missing or default ('dev') SECRET_KEY, enabling session hijacking and cookie forgery.
**Learning:** Checking for configuration constraints (like SECRET_KEY) inside the class body of a configuration class (e.g. `ProductionConfig`) executes at import time, breaking local development and test discovery. The check must be deferred to the application factory (`create_app()`).
**Prevention:** Always validate critical security parameters like `SECRET_KEY` inside the application factory after loading configuration, checking `app.debug is False and app.config.get('TESTING') is False` to avoid breaking dev/test environments.
