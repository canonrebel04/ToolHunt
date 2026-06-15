## 2025-06-15 - Hardcoded Secret Key in Application Configuration
**Vulnerability:** A hardcoded default 'change-this-in-production' secret key was found in the ProductionConfig within app/config.py.
**Learning:** Default Flask applications or templates often include placeholder string secrets to enable quick local testing, but these placeholders frequently mistakenly make their way into production configurations.
**Prevention:** Utilize environment variables (e.g., `os.environ.get('SECRET_KEY')`) systematically across deployment configurations rather than static strings to enforce the injection of secure, unique keys at runtime.
