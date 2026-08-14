## 2024-05-20 - [List index optimization in Python]
**Learning:** Using `list.index(item)` in a loop results in O(N^2) complexity.
**Action:** Replace `list.index()` loops with O(1) dictionary lookups, keeping first occurrences logic if list has duplicates.
