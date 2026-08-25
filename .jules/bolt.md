## 2025-02-22 - Optimize find_indices with O(1) Dictionary Lookup
**Learning:** Replaced an O(M * N) list.index() lookup with an O(N + M) dictionary lookup which drastically improved time complexity for larger lists without altering test behaviors. The trick with handling duplicate values efficiently when transitioning away from list.index() was utilizing an `if item not in lookup: lookup[item] = idx` structure.
**Action:** Apply this dictionary lookup optimization anytime list elements are searched multiple times within an outer loop to reduce redundant scanning overhead.
