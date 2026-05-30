## 2024-05-30 - Object Identity Fast Path and Dict Creation Overhead

**Learning:** When attempting to optimize an $O(N \cdot M)$ list scan (`list.index()` inside a loop) using a hash map, creating the map on the fly inside the function ($O(N)$) can actually be slower than the naive array scan if $M$ is very small. In ToolHunt, scanning 2,860 items 10 times with native C `.index()` takes ~0.33ms, whereas creating a 2,860-item Python dictionary on the fly takes ~0.47ms.

**Action:** For static datasets like the tool descriptions list, the optimal pattern is to construct the hash map *once* during load time (caching it globally) and use Python's fast object identity `is` operator to verify if the incoming list matches the cached list (`if primary_list is _descriptions`). This drops the lookup time to $O(M)$ (essentially 0.001ms, a ~190x speedup) while maintaining full fallback compatibility for other lists.
