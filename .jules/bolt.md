## YYYY-MM-DD - Optimize Pagination Slice
**Learning:** When implementing or modifying pagination logic, always apply the pagination slice (e.g., [offset:offset+limit]) to the raw result set before performing any expensive data transformations or JSON formatting.
**Action:** This ensures O(limit) time complexity rather than O(total).
