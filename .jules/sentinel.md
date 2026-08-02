## 2025-02-23 - Hardcoded Flask Secret Key
**Vulnerability:** Hardcoded Flask SECRET_KEY in configuration files.
**Learning:** Hardcoding a secret key in version control exposes the application to session hijacking. The key should always be dynamically loaded from the environment with a secure, random fallback if none is provided.
**Prevention:** Use `os.environ.get('SECRET_KEY', secrets.token_hex(32))` to securely configure the secret key in Flask applications and avoid committing secrets in code.
