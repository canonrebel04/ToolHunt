## 2024-07-10 - Fixed Hardcoded Secret Key
**Vulnerability:** The Flask application's `SECRET_KEY` was hardcoded to a static string in both development and production configurations.
**Learning:** Hardcoded secret keys allow attackers to forge session cookies or tamper with signed data.
**Prevention:** Always use environment variables for sensitive configuration values, and enforce their presence in production configurations.
