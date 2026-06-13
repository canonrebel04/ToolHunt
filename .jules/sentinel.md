## 2024-06-13 - Hardcoded Secret Key in Production Config
**Vulnerability:** Hardcoded `SECRET_KEY = 'change-this-in-production'` in `ProductionConfig` could lead to compromised sessions or other secret-key-based crypto attacks if deployed to production without modification.
**Learning:** Configurations shouldn't contain default values for sensitive keys in production classes, since users might deploy them without changing the value, leading to severe security risks.
**Prevention:** Use environment variables (e.g., `os.environ.get('SECRET_KEY')`) for sensitive configuration variables to force operators to inject secrets safely at runtime rather than relying on source code defaults.
