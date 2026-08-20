## 2024-08-20 - Unsafe Production Default SECRET_KEY
**Vulnerability:** A fallback `SECRET_KEY` of `dev` or generated value was potentially being used for production.
**Learning:** Raising an exception in the configuration class executes at import time and fails during test discovery; it must be verified at application startup in `create_app`.
**Prevention:** Always enforce production-only constraints at runtime inside the application factory or runtime initialization step.
