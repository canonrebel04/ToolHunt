## 2026-06-01 - Fix hardcoded secret in config
**Vulnerability:** Hardcoded SECRET_KEY placeholder `'change-this-in-production'` in `app/config.py` for `ProductionConfig` instead of reading from environment variables.
**Learning:** Found a hardcoded secret configuration fallback directly within the checked-in source code, a serious vulnerability if not correctly populated during deployment.
**Prevention:** Always use `os.environ.get('SECRET_KEY')` instead of a string literal fallback for production secrets, forcing the environment to explicitly supply it.
