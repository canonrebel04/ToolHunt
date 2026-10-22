## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Accessible Disabled Anchor Tags]
**Learning:** Suppressing interactions on disabled anchor tags with `pointer-events: none` is an accessibility anti-pattern because it suppresses hover events, preventing tooltips from appearing. Additionally, `.textContent` correctly ignores icon elements, so slicing the text can inadvertently truncate valid multi-word input.
**Action:** Always use `cursor: not-allowed`, `aria-disabled="true"`, `tabindex="-1"`, and `onclick="return false;"` for disabled links while providing a tooltip to explain the disabled state.
## 2026-10-12 - [Accessible Alerts]
**Learning:** Found that alert messages lacked ARIA roles, preventing screen readers from automatically announcing them to the user.
**Action:** Always add `role="alert"` and `aria-live="assertive"` to dynamically created alert messages.
## 2026-10-13 - Actionable Empty States
**Learning:** Users who encounter zero search results often abandon the search if the suggestions are just static text. Converting static examples into clickable actions directly reduces friction and helps users discover valid content faster.
**Action:** Always make empty state suggestions interactive components (like buttons or links) that trigger the suggested action immediately.
## 2026-10-14 - Screen Reader Context for External Links
**Learning:** When using target="_blank" for external links, visual users see a new tab open, but screen reader users lose context entirely. Using a visually-hidden span like `<span class="visually-hidden">(opens in a new tab)</span>` preserves this critical navigation context for non-visual users.
**Action:** Always append visually hidden text to indicate external link behavior, and pair it with rel="noopener noreferrer" for security.

## 2026-10-15 - [Defensive Event Listener Binding]
**Learning:** Found that directly calling `addEventListener` on elements queried by ID causes a crash if the element is missing from the DOM, breaking all subsequent JS logic.
**Action:** Always wrap event listener bindings in an `if (element)` check or check if the element exists before adding event listeners to prevent breaking the script if the UI component is removed or missing.
## 2024-05-24 - Hiding decorative icons in aria-live regions
**Learning:** When injecting dynamic content into aria-live regions, screen readers will redundantly read the class names or unicode values of font-awesome icons if they are not explicitly hidden, causing excessive noise.
**Action:** Always ensure dynamically injected decorative icons include `aria-hidden="true"` within JavaScript template literals.

## 2024-06-25 - [Inline Validation and Focus Management]
**Learning:** Found that showing an alert for an empty search query is insufficient for accessibility, as users may not immediately know which field is invalid. Setting `aria-invalid` and immediately shifting focus back to the input ensures screen reader users are properly guided.
**Action:** Always use `aria-invalid="true"`, visual cues, and focus management (shifting focus to the invalid field) for inline form validation.
