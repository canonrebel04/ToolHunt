## 2026-10-01 - Global Cache Thread Safety
**Learning:** Populating global caches dynamically in concurrently called functions without protection introduces race conditions.
**Action:** Always initialize and populate caches during a thread-safe startup phase inside an existing double-checked lock, and assign the global indicator variable last.
