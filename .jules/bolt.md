## YYYY-MM-DD - Cache dict for O(1) index lookups
**Learning:** Rebuilding a dictionary on every function call for O(1) lookup effectively negates the O(1) benefit and turns the operation into O(N). By precomputing the dictionary once and caching it at the module level, we achieve true O(1) performance.
**Action:** Always consider the cost of constructing data structures inside hot paths and cache them globally or at startup if they are immutable.
