## 2025-05-18 - Optimized list lookup in backend

**Learning:** `list.index()` calls inside a loop result in O(n*m) complexity.
**Action:** Always consider replacing nested loop searches with an O(n) hash map lookup, utilizing enumerate to track indices, ensuring O(1) retrieval time.
