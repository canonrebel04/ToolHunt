## 2023-10-24 - O(N^2) list.index() in tool search
**Learning:** Using `list.index()` inside a loop for searching matches degrades performance to O(N^2), especially when querying against thousands of tool descriptions.
**Action:** Replace `list.index()` loops with O(1) hash map lookups, iterating to only store the first index to match the original behavior exactly.
