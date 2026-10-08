## 2024-03-22 - Optimize find_indices to be O(1) index caching cache
**Learning:** Found a function find_indices which is creating dictionary for cache indexing inside the function but the dictionary could be pre-calculated and cached at the module level.
**Action:** When implementing caching for performance optimizations in concurrent applications, initialize and populate the cache during a thread-safe startup phase and treat it as read-only thereafter.
