## 2024-05-18 - List Index Lookups
**Learning:** Using `list.index()` inside a loop for list intersections results in O(n^2) time complexity which becomes a bottleneck on larger datasets.
**Action:** Replace nested `list.index()` lookups with an O(n) hash map (dictionary) built using `enumerate()` to preserve first-occurrence behavior.
