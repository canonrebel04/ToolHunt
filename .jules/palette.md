## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## 2024-03-22 - Missing ARIA hidden attributes on decorative icons
**Learning:** Decorative icons (like Font Awesome `<i>` tags) that accompany text or are purely visual need `aria-hidden="true"` to prevent screen readers from announcing them redundantly, which clutters the accessibility tree.
**Action:** Always ensure that purely decorative icons have `aria-hidden="true"`, especially when they are used alongside descriptive text.
