## 2024-06-12 - Hardcoded Secret Key in Production Config
**Vulnerability:** A hardcoded `SECRET_KEY` was found in `ProductionConfig` in `app/config.py`.
**Learning:** Hardcoded secrets in version control can lead to application compromise if the repository is leaked or accessed by unauthorized individuals.
**Prevention:** Use environment variables like `os.environ.get("SECRET_KEY")` to securely manage secrets in production.
