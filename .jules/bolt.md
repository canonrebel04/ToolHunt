## YYYY-MM-DD - Pre-computing dictionaries during startup
**Learning:** Building dictionary lookups during hot paths (per-request) adds significant overhead for large datasets. Re-hashing the same static list on every search request takes O(N) time.
**Action:** Always pre-compute static lookups (like list-to-index mappings) during the initial thread-safe setup phase (e.g., inside double-checked locks) and cache them as read-only globals.
