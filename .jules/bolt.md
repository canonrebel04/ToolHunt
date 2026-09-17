## YYYY-MM-DD - [Optimize result formatting before slicing]
**Learning:** Formatting all search results into dictionaries before applying pagination offset/limit causes O(N) work, which scales poorly when many tools match the query. Slicing the raw tuple list first reduces it to O(limit) work.
**Action:** Apply pagination slices to raw data streams before mapping them into final response dictionaries.
