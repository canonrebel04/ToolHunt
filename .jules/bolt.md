## 2024-05-15 - Fast-path O(1) Lookups for Static Arrays
**Learning:** For static module-level datasets, using Python's `is` operator to check identity (`primary_list is _descriptions`) allows using a pre-computed hash map for O(1) lookups, providing a fast-path without penalizing generic list lookups with on-the-fly dictionary creation overhead.
**Action:** Always check if a target array in an O(N^2) search is actually a static/cached variable, and if so, pre-compute a hash map for it and add an identity-based fast-path.
