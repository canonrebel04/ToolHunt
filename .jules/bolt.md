## 2025-06-30 - Optimize find_indices function
**Learning:** `list.index()` inside a loop can be a performance bottleneck with O(N*M) complexity, but we need to correctly emulate its behavior of finding the *first* occurrence of duplicate elements. Creating an intermediate list using `reversed(list(enumerate()))` is memory-inefficient for large lists.
**Action:** Replaced it with an O(1) dictionary lookup. To preserve memory and correctly handle duplicates by returning the first index, a simple `for` loop `if val not in primary_map: primary_map[val] = idx` is much better.
