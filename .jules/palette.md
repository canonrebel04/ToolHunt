## 2024-08-28 - Missing ARIA Attributes on Disabled Links
**Learning:** Using `href="#"` and inline CSS to disable links is insufficient for screen readers; they still interpret it as a focusable link. Setting `aria-disabled="true"`, omitting the `href` completely, and using `role="link"` ensures correct assistive tech behavior while avoiding focus traps.
**Action:** When conditionally disabling links, omit the `href` attribute, add `aria-disabled="true"`, and use `role="link"` to maintain link semantics.
