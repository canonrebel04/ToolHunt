## 2024-07-03 - [Optimize find_indices in backend/main.py]
**Learning:** The `find_indices` function in `backend/main.py` uses `list.index()` inside a loop, which makes it an O(n*m) operation. With a large primary list (e.g. 2860 tools), searching for many matching elements can be slow.
**Action:** Replace `list.index()` with an O(1) dictionary lookup by precomputing an index map, while maintaining the first-occurrence behavior of `.index()` by only adding to the dictionary if the element is not already present.
