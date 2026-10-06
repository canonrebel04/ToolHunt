## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## 2024-05-16 - Disabled Link Accessibility
**Learning:** Using `pointer-events: none` on disabled links completely suppresses hover events, which prevents native tooltips (via `title`) from showing, confusing users about why the link is inactive.
**Action:** Instead of `pointer-events: none`, use `cursor: not-allowed`, add `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` to properly style, communicate, and enforce the disabled state while preserving hover capability for tooltips.
