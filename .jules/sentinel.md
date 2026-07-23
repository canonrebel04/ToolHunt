## 2025-02-14 - Hardcoded Secret Key
**Vulnerability:** Hardcoded Flask `SECRET_KEY` in `app/config.py` for both development and production.
**Learning:** Found hardcoded secret keys that can allow attackers to forge session cookies and other cryptographically signed data.
**Prevention:** Always use environment variables for sensitive configuration like secret keys, with a secure random fallback for local development if appropriate (e.g., `os.environ.get('SECRET_KEY', secrets.token_hex(32))`).
