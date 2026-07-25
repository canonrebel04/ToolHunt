## 2025-05-15 - Replace O(n^2) nested loop with O(n) hash map lookup
**Learning:** Found an `O(N * M)` list index lookup inside `find_indices` in `backend/main.py`. This is called after every search query to map string descriptions back to the main data store. In Python, `.index()` does a linear scan, so looping over M query items on an N-sized list is extremely inefficient as the database grows.
**Action:** Use a dictionary hash map for O(1) lookups during index mapping to reduce complexity to `O(N + M)`.
