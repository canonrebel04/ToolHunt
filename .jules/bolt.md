## 2024-03-21 - Caching Index Lookup
**Learning:** In highly concurrent applications, rebuilding lookup indexes (e.g., dicts) inside frequently called functions is a performance bottleneck.
**Action:** Pre-compute the lookup index globally during a thread-safe startup phase (e.g., lazy loading) to achieve zero-cost O(1) lookups on the fast path.
