## 2025-05-27 - Input Validation on Pagination Endpoint
**Vulnerability:** Resource Exhaustion (DoS) risk and TypeErrors in the `/search` API endpoint due to lack of strict type casting and boundary checks on pagination parameters (`limit` and `offset`).
**Learning:** External inputs mapped directly to database query slices must always be validated and bound-checked to prevent clients from requesting excessively large result sets or triggering internal server errors.
**Prevention:** Implement strict type casting (e.g., `int()`) and enforce tight boundaries (e.g., max limit of 100) on all incoming pagination requests, failing securely with a 400 Bad Request error.
