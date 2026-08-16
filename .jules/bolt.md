## 2025-09-04 - O(N*M) list lookups
**Learning:** Found a critical performance bottleneck in Python `list.index()` being used inside a loop to lookup matching items. `list.index()` has O(N) complexity and doing it M times makes it O(N*M).
**Action:** Replace `list.index()` inside loops with O(1) dictionary lookups by pre-computing indices mapping for an O(N+M) total complexity. Make sure to use `if item not in dict:` to preserve exact parity with `list.index()` returning the first match.
