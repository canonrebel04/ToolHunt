## 2025-09-04 - O(N) list search in search_tool
**Learning:** `list.index(query_item)` inside a loop over `query_list` gives O(N*M) time complexity. Optimizing `find_indices` with O(1) dictionary lookup provides a modest speedup.
**Action:** Always prefer O(1) dictionary lookup when searching multiple items in a large list, but remember to preserve the behavior of `.index()` handling duplicates (finding first occurrence) and missing items without raising exceptions.
