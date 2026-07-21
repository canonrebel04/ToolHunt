## 2025-02-27 - Hardcoded Flask Secret Key
**Vulnerability:** Flask `SECRET_KEY` was hardcoded in both base `Config` ('dev') and `ProductionConfig` ('change-this-in-production').
**Learning:** This could allow attackers to forge session cookies or guess CSRF tokens if the production environment failed to override the configuration securely.
**Prevention:** Always use `os.environ.get('SECRET_KEY', secrets.token_hex(32))` in base configs and enforce its presence via a validation check (e.g., `raise ValueError` if missing) in the application factory when starting in production mode.
