## 2024-05-20 - Initial Setup\n**Learning:** Starting performance optimizations for ToolHunt.
## 2026-08-22 - Replace O(N^2) list.index() in loop with O(N) hash map lookup
**Learning:** Found a nested loop O(N^2) complexity where .index() was called on a list of 2800 items for each matching result. O(N^2) scaling is bad.
**Action:** Replaced with O(N) dictionary lookup, maintaining 'first index' matching.
