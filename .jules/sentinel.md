## 2026-08-23 - Prevent default SECRET_KEY in production
**Vulnerability:** The Flask application could start in production with a weak default 'dev' SECRET_KEY if the environment variable was missing.
**Learning:** Enforcing configuration constraints like a mandatory SECRET_KEY must be done in the application factory (create_app) rather than class bodies to prevent import-time exceptions during testing/development.
**Prevention:** Always validate critical security configurations during app initialization, checking against debug/testing flags to differentiate environments.
