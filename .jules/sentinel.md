## 2025-05-28 - Hardcoded Production Secret Key
**Vulnerability:** A hardcoded Flask Production Secret Key could lead to session hijacking, cross-site request forgery (CSRF), and other attacks if deployed as-is.
**Learning:** Hardcoded placeholders such as 'change-this-in-production' often end up in production unchanged.
**Prevention:** Always use environment variables for sensitive settings like `SECRET_KEY` in production configurations, such as by retrieving them with `os.environ['SECRET_KEY']`.
