## YYYY-MM-DD - Cache Static Lookup Dictionaries
**Learning:** Generating a lookup dictionary on every search request inside find_indices causes unnecessary overhead since the primary list (_descriptions) is static.
**Action:** Initialize the lookup dictionary during startup (_load_tools) and cache it globally for O(1) lookups on subsequent searches without recomputing.
