## YYYY-MM-DD - Global Index Caching in Thread-Safe Setup
**Learning:** When implementing caching for performance optimizations in concurrent applications, initializing and populating the cache inside an existing double-checked lock and treating it as read-only prevents race conditions and makes lookups O(1) across the entire application runtime.
**Action:** Initialize globally-cached index mappings during thread-safe setup to avoid repeating work or dynamically modifying globals.
