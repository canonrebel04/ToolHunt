## YYYY-MM-DD - Apply pagination slice before data transformation
**Learning:** Formatting the entire result set before pagination slicing causes O(N) complexity where N is the total result size, introducing unnecessary latency on large data sets.
**Action:** Always apply the pagination slice (e.g. [offset:offset+limit]) to the raw result set *before* performing expensive transformations or JSON formatting to ensure O(limit) time complexity.
