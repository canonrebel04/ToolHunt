## 2024-03-21 - [Optimize Dictionary Build in Search Tool]
**Learning:** When implementing O(1) lookup caching for performance optimizations in concurrent applications, dynamically updating unprotected global dictionaries inside frequently called functions (like `find_indices`) wastes CPU and introduces thread-safety risks.
**Action:** Initialize and populate lookup caches during the existing double-checked locked startup phase (`_load_tools`) and treat them as read-only thereafter.
