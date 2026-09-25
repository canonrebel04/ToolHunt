## YYYY-MM-DD - [Precompute dictionary mapping for O(1) lookups]
**Learning:** Rebuilding a dictionary on every function call for a large list (2860 elements) is a performance bottleneck.
**Action:** Move the dictionary construction to the lazy-load initialization step and cache it globally. This reduced the lookup time from O(N*M) to O(1) in the hot path.
