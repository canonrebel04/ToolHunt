## 2025-05-18 - Optimized list lookups in repeated function calls
**Learning:** In scenarios where a large list is queried repeatedly but isn't modified (such as a lazy-loaded list of 2800 descriptions), rebuilding a dictionary for O(1) lookups on every function call is an unnecessary performance bottleneck. Identity checks (`is`) are significantly faster than equality checks (`==`) for verifying if the list is still the same object.
**Action:** Use a global cache and an `is` check to memoize dictionaries built from static lists to speed up O(N) lookup operations across multiple calls.
