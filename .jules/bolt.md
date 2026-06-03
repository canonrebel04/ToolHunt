## 2024-06-03 - O(1) Tool Lookup Optimization
**Learning:** Python's array `.index()` runs in O(N) time and was causing performance bottlenecks when finding indices for multiple returned searches during the `search_tool` process in `backend/main.py`. This issue arose because tool descriptions are stored statically after the module lazy-loads, but lookups were still sequential arrays.
**Action:** Use Python's `is` operator to determine if the array being searched is the globally cached module-level list, and if so, fall back to a precomputed O(1) dictionary hash-map `_description_to_index`.
