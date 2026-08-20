## 2024-05-18 - [Optimization learning]\n**Learning:** Initial optimization\n**Action:** Optimize find_indices
## 2026-08-20 - [O(N^2) list.index() in search path]
**Learning:** The `find_indices` function used `list.index()` inside a loop, resulting in O(N^2) performance when matching query results to the main tool list. This is a common bottleneck in search applications dealing with large lists.
**Action:** Use a pre-computed dictionary for O(1) lookups instead, but carefully handle duplicates by only inserting the first occurrence to maintain exact parity with `list.index()`.
