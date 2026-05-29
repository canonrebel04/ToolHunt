## 2024-05-18 - Hardcoded Production SECRET_KEY in Configuration
**Vulnerability:** The ProductionConfig in `app/config.py` contained a hardcoded `SECRET_KEY = 'change-this-in-production'`.
**Learning:** Hardcoded secrets in version control are a critical risk as attackers can use them to forge session cookies or tamper with cryptographic signatures in production deployments.
**Prevention:** Always enforce environment variables for sensitive configuration variables in production configurations (e.g. `os.environ['SECRET_KEY']`). For tests to run correctly, set a mock environment variable early (e.g., in the pytest `pytest_configure` hook) before module import paths evaluate the configuration file.
