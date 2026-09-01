## YYYY-MM-DD - Precompute Static Lookups
**Learning:** The previous optimization changed O(N) list.index() to O(1) dict lookup, but rebuilt the dict on EVERY request (O(N) time per request). Since the tool dataset is static after lazy-loading, the lookup dictionary should be precomputed once.
**Action:** Always check if the data being iterated over to build a cache is actually static across requests. If so, move the cache building to the initialization/load phase.
