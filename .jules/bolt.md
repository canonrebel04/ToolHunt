## 2026-08-28 - O(N^2) list.index in loops
**Learning:** Using `list.index(item)` inside a loop over another list creates an O(N*M) bottleneck, as it scans the primary list from the start for every query item.
**Action:** Always replace `list.index()` in loops with an O(N) pre-computed dictionary lookup using a standard loop with `if item not in lookup:` to map first occurrences when dealing with large lists.
