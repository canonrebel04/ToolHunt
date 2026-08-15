## $(date +%Y-%m-%d) - [O(n^2) to O(n) Optimization in find_indices]
**Learning:** Using `list.index(item)` in a loop creates an O(n^2) operation because `list.index` requires O(n) search per iteration. This is a common bottleneck in matching or mapping operations.
**Action:** When finding multiple indices of queried items in a main list, build a hash map (dictionary) of `item -> first_index` in O(n) time, then look up query items in O(1) time each, reducing total complexity to O(n).
