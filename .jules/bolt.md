## 2025-06-22 - Optimize O(n^2) loop with cached hash map

**Learning:** Creating a hash map cache during lazy load initialization and using an `is` memory-identity check inside generic methods is an effective way to optimize O(n^2) loops (like list.index() in a loop) for static module-level datasets without paying dictionary creation overhead on dynamic lists.
**Action:** When iterating with `.index()` over a static primary list that is repeatedly queried, build a hash map cache of its indices at load time to achieve O(1) lookup. When duplicates exist, reverse iterate the enumeration so earlier items override later ones, matching standard `.index()` behavior.
