## 2025-09-04 - Hardcoded Secret Key
**Vulnerability:** Hardcoded `SECRET_KEY` values ('dev' and 'change-this-in-production') were found in `app/config.py` in the `Config` and `ProductionConfig` classes.
**Learning:** These values are committed directly into the source control and are deployed with the application. Anyone with read access to the code can use them to forge or tamper with session cookies.
**Prevention:** Use an environment variable with a secure fallback (e.g. `os.environ.get('SECRET_KEY', secrets.token_hex(32))`) instead of hardcoded strings to prevent sensitive credentials from being committed to the repo, ensuring unconfigured environments are safe.
