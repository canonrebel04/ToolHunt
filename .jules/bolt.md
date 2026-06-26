## 2025-09-04 - O(1) Index Map caching
**Learning:** In `backend/main.py`, the application maps search result strings back to database objects by invoking `list.index()` over all 2,860 rows for every single result. This creates an O(M * N) bottleneck inside `find_indices` during the critical path of the search API.
**Action:** Using a pre-computed O(1) hash map built during the lazy load phase, alongside the original `_descriptions` list, speeds up post-retrieval ID mapping without adding to query latency. Reversed enumeration preserves identical behavior for handling duplicates.
