## 2026-05-28 - Missing Validation Leading to DoS via Unhandled Exceptions
**Vulnerability:** The `/search` endpoint blindly accepted `limit` and `offset` as any type, leading to unhandled TypeErrors when strings or negative integers were passed.
**Learning:** Python type hinting does not enforce runtime parameter safety for Flask JSON payloads. If unchecked, exceptions during slice operations or third-party library calls (like FAISS) result in 500 Internal Server Errors, which could be abused for resource exhaustion/DoS.
**Prevention:** Always explicitly cast numerical JSON parameters to `int()`, catch `ValueError`/`TypeError` returning 400 Bad Request, and strictly enforce min/max bounds (e.g., `limit = max(1, min(100, limit))`).
