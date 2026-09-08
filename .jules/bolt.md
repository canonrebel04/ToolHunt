## 2024-03-21 - Race Conditions with Double-Checked Locking
**Learning:** When adding globally cached data structures in a function using double-checked locking, the indicator variable (e.g., `_tools`) must be assigned LAST. Assigning it before populating the new data structures creates a race condition where other threads can read incomplete data.
**Action:** Always ensure the indicator variable is the final assignment in double-checked locking setups.
