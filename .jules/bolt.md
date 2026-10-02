## YYYY-MM-DD - Precomputing Static Dictionaries
**Learning:** Rebuilding a dictionary dynamically inside a frequently called function creates an O(N) bottleneck per search.
**Action:** Precompute static O(1) lookup dictionaries during the thread-safe startup phase.
