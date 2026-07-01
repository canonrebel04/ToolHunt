## 2024-07-01 - Prevent Exception Detail Leakage in API Responses
**Vulnerability:** The application was exposing raw exception strings (`str(e)`) to the client in the `/health` and `/search` API endpoints upon encountering an error. This can lead to information disclosure vulnerabilities where internal system details, paths, or database structures are leaked to potential attackers.
**Learning:** Exception handling routines were directly passing the caught exception object's string representation into the JSON response payloads.
**Prevention:** Always log the full exception details server-side using `logger.exception()` for debugging, but return generic, sanitized error messages (e.g., "An error occurred", "Database check failed") to the client.
