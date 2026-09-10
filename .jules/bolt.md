## 2026-09-10 - [RRF Time Complexity Optimization]
**Learning:** The initial RRF implementation used O(N) operations involving multiple dictionary comprehensions and iterative lookups to fuse arrays which is slower than updating scores in a single hash map pass.
**Action:** Replaced iterative array-to-dict merges with an in-place aggregation to improve hybrid search speed, avoiding multi-pass loops.
