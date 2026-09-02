## 2025-03-04 - Optimize RRF Dictionary Lookups
**Learning:** When combining scores from two ranked lists (like FAISS and BM25), building separate rank dictionaries, then an aggregated unique document dictionary, and iterating through values causes redundant lookups and object allocations. We can optimize this by aggregating the RRF score natively in a single pass through each list.
**Action:** Direct single-pass accumulation is faster than building intermediate rank lookup dictionaries.
