## 2024-05-30 - Fix hardcoded SECRET_KEY in ProductionConfig
**Vulnerability:** The ProductionConfig class hardcoded the `SECRET_KEY` variable as "change-this-in-production".
**Learning:** Hardcoded secrets in production configuration classes can easily be checked into version control, posing a major risk of credential leakage.
**Prevention:** Use `os.environ.get("SECRET_KEY")` or similar environment variables to inject sensitive data at runtime.
