## YYYY-MM-DD - Cache index lookup globally
**Learning:** When implementing caching for performance optimizations in concurrent applications, do not dynamically update unprotected global variables within frequently called functions, as this introduces severe thread-safety bugs (e.g., race conditions overwriting the cache). Instead, initialize and populate the cache during a thread-safe startup phase (e.g., inside an existing double-checked lock) and treat it as read-only thereafter.
**Action:** Initialize globally cached dictionaries once during thread-safe startup phases.
