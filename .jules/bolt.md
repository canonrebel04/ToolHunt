## YYYY-MM-DD - Moving Index Build to Module Load
**Learning:** In backend/main.py, find_indices builds a primary_dict on every call, taking O(N) time. By moving this build step to the lazy module load _load_tools, we make the cache persistent and reduce lookup time to O(1) for every subsequent search.
**Action:** When implementing caching for index lookup, always move the dictionary generation to the module's setup or initialization phase rather than doing it per-call.
