## 2025-05-20 - Adding Disabled State During Search
**Learning:** The "Hunt Tools" button does not disable itself or show a loading state during the async search operation. This can lead to users double-clicking and spamming the backend, as well as a lack of immediate feedback.
**Action:** Add a disabled state to the button while the search is in progress, potentially swapping the icon to a spinner.
