## YYYY-MM-DD - Caching static index maps globally
**Learning:** Rebuilding a lookup dictionary for a static dataset (2,860 elements) inside the request path added ~0.4ms per query overhead. Even if it's O(N) instead of O(N*M), O(N) per request adds up.
**Action:** For completely static data loaded once at startup, compute and cache the O(1) lookup dictionary globally rather than rebuilding it on the fast path.
