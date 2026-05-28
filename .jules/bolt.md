## 2024-05-28 - Optimize backend list search from O(N²) to O(1)
**Learning:** `list.index(item)` inside a loop over search results scales at O(N * M), creating a bottleneck during tool lookups in `backend/main.py` when `_descriptions` contains ~2,860 entries.
**Action:** When finding indices of elements from one large list in another, always construct an O(1) lookup hash map `(dict)` during data loading instead of using repeated `list.index()` calls.
