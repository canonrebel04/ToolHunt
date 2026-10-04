## YYYY-MM-DD - Cache Lookup Global on Hot Path
**Learning:** When implementing caching for performance optimizations in concurrent applications, dynamically updated dictionaries on the hotpath should be replaced by a globally cached dictionary constructed at startup.
**Action:** Initialize and populate lookup cache during thread-safe startup phase and treat as read-only on hot path.
