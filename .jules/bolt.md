## YYYY-MM-DD - Global Cache for Index Lookup
**Learning:** Rebuilding a dictionary lookup for O(N) items dynamically per request can be a massive bottleneck, even if it claims to be caching index lookups internally. The fix is moving this cache calculation to the global lazy-loading stage.
**Action:** When a cache lookup is built for a fixed global resource, ensure the lookup map itself is cached globally, not rebuilt locally on every request.
