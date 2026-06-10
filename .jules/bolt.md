# Bolt's Performance Learnings

## 2026-06-10 - O(1) hash map fast-path without penalizing dynamic lists
**Learning:** For functions that operate on both module-level static lists and dynamic arrays, utilizing `is` operator checks (e.g., `primary_list is _descriptions`) ensures O(1) lookups via a precomputed hash map for the static data, bypassing native O(N) array scans, without paying the cost of creating a hash map on-the-fly for small, dynamic query arrays.
**Action:** Next time when iterating arrays and performing `.index()` lookups on known long constant lists (like a dataset of 2,860 entries), use a global precomputed map to short-circuit the linear scan when the array passed matches the global identity.
