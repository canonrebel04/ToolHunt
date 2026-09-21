## 2025-01-20 - Global caching avoids N allocations
**Learning:** In backend/main.py, find_indices rebuilt a 2,860-item dictionary on every search query just to reverse-map a list. Caching this mapping globally during initial load saved significant memory allocation overhead on every search.
**Action:** Pre-compute reverse lookup dictionaries globally or at startup for static data instead of per-request.
