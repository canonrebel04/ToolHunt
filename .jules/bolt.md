## 2026-10-01 - Global Cache Thread Safety
**Learning:** Populating global caches dynamically in concurrently called functions without protection introduces race conditions.
**Action:** Always initialize and populate caches during a thread-safe startup phase inside an existing double-checked lock, and assign the global indicator variable last.

## 2026-10-12 - DOM Reflows in Result Rendering
**Learning:** Appending individual DOM elements directly to a live container inside a loop causes multiple expensive layout recalculations (reflows) and repaints, creating a performance bottleneck for rendering large result lists.
**Action:** Always batch DOM updates by appending elements to a `DocumentFragment` first, and then appending the fragment to the live DOM in a single operation.
