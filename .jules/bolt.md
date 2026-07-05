## 2023-10-25 - [O(n^2) loop replacement]
**Learning:** Found an O(n^2) nested lookup pattern inside `find_indices` using `list.index()` over a large dataset.
**Action:** Replace `primary_list.index()` with an O(n) hash map (dictionary) creation and lookup to significantly reduce time complexity on large collections.
