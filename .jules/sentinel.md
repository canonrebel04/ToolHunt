## 2024-05-15 - Do not leak exceptions in API responses
**Vulnerability:** Raw exception strings (`str(e)`) were being returned directly in JSON API responses (`/health` and `/search` endpoints). This is an Information Disclosure vulnerability.
**Learning:** Returning `str(e)` directly exposes internal stack traces, system paths, or database structures which attackers can use to gather intelligence for targeted attacks.
**Prevention:** Always log the full exception internally (using `logger.exception`), but return a generic, static error message to the client, such as "An internal error occurred."
