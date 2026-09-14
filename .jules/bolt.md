# Bolt's Performance Learnings
## 2024-03-21 - [Time Complexity Mirage in Local Caching]
**Learning:** A local dictionary lookup optimization in `find_indices` created an O(1) retrieval but suffered from O(N) dictionary rebuilding costs on every search query, creating a performance mirage where it was still bounded by O(N+M). Additionally, when using double-checked locking, assigning the global indicator variable before other global variables causes race conditions on the fast path.
**Action:** Globally cache the index mapping at module startup (O(1) lookup with zero per-request rebuild cost) and always assign the double-checked locking indicator variable last.
