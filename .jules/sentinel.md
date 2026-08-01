## 2025-05-24 - [Fix hardcoded secrets]
**Vulnerability:** Hardcoded Flask `SECRET_KEY`s (`'dev'` in the base config, and `'change-this-in-production'` in the production config) in `app/config.py`.
**Learning:** Hardcoded secrets in configuration files can easily compromise session security and gain access to user data if the source code or configurations are leaked.
**Prevention:** Always use environment variables to manage application secrets, and implement a cryptographically secure fallback (e.g. `secrets.token_hex(32)`) to ensure the application remains secure even if the environment variable is accidentally omitted.
