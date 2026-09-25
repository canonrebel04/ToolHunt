## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## 2025-09-25 - [Accessible Disabled Anchor Tags]
**Learning:** Using `pointer-events: none` on anchor tags hides them from hover events, meaning users with mice won't see tooltips explaining why they are disabled. It also doesn't prevent keyboard navigation natively without tabindex and aria-disabled.
**Action:** When disabling anchor tags, use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` to maintain accessibility while preventing interaction.
