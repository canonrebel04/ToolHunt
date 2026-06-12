
## 2024-05-24 - [O(n²) array search bottleneck]
**Learning:** `list.index()` used within a loop created an O(n²) bottleneck because it performs a linear O(n) scan for each query element over the primary list.
**Action:** Replace `list.index()` loops with an O(1) hash map lookup, and ensure the hash map is built efficiently iteratively in reverse if the first-occurrence behavior is required. For static module-level lists, caching the map with the lazy loader avoids dictionary creation overhead on every call.
