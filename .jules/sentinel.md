## 2024-05-27 - Hardcoded Flask Secret Key
**Vulnerability:** A hardcoded Flask `SECRET_KEY` was found in `app/config.py`. If an attacker gains access to this code, they could use this key to forge session cookies or bypass CSRF protections, compromising user sessions and potentially leading to account takeover.
**Learning:** Never hardcode sensitive credentials, such as secret keys, in the source code.
**Prevention:** Always read secret keys from environment variables or a secure secret management system, ensuring they can be set differently for each environment without modifying the code.
