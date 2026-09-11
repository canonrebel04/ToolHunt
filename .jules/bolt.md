## YYYY-MM-DD - Python Global Variable Scoping in Lazy Loading
**Learning:** When adding a new module-level cache variable that gets populated inside a lazy-loaded function, failing to add it to the explicit `global` declaration causes Python to treat the assignment as a local variable. This results in the module-level variable remaining `None`, causing a `TypeError` when other functions try to use it.
**Action:** Always verify that newly introduced module-level caching variables are explicitly declared in the `global` statement of the loading function before assignment.
