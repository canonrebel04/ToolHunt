## 2024-10-10 - O(1) Pagination Formatting
**Learning:** Pagination logic applying slice after JSON formatting results in O(N) formatting instead of O(M) where M is the limit.
**Action:** Apply slice first on all_results, then format only the items being returned.
