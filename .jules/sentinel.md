## 2026-08-21 - Enforce Production Flask Configuration
**Vulnerability:** Flask app could start in production without a valid SECRET_KEY.
**Learning:** Raising exceptions in config class bodies breaks test discovery. Evaluating config_class.__name__ is unreliable. Validation must occur inside the app factory after loading.
**Prevention:** Validate critical configurations inside create_app(), identifying production by evaluating app.debug and app.config['TESTING'].
