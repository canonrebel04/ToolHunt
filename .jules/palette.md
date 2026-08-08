## 2023-10-27 - Disabled Button State during async searches
**Learning:** Preventing duplicate requests and providing visual feedback during search is essential for an intuitive experience. Using `disabled` and `aria-disabled="true"` natively provides both visual styling hooks and accessibility markers.
**Action:** When implementing async search, always disable the search button while loading, and style the disabled state explicitly.
