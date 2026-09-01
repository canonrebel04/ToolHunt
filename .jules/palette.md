## 2024-05-18 - Disabled links accessibility
**Learning:** Using pointer-events: none on an anchor tag makes it entirely invisible to screen readers without communicating disabled state. Conditionally rendering a span with aria-disabled="true" provides much better context.
**Action:** Always swap out anchor tags for visually-styled span/button equivalents when the link destination is missing or disabled.
