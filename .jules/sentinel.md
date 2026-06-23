## 2024-05-24 - API Information Disclosure via str(e)
**Vulnerability:** Raw exception strings (`str(e)`) were being returned directly in JSON responses for `/health` and `/search` endpoints.
**Learning:** This exposes internal application errors and potentially sensitive state or stack trace information to the client, which can be leveraged for further attacks.
**Prevention:** Always log the actual exception internally using a logger, and return a generic, safe error message (e.g., "An internal error occurred") to the user.
