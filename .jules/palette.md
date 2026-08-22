## 2024-05-24 - Screen Reader & Keyboard Access for Disabled Links
**Learning:** CSS `pointer-events: none` does not prevent keyboard navigation on `<a>` tags if they have an `href` attribute. Screen reader and keyboard users can still tab to and interact with them, leading to confusing top-of-page scrolling or broken links.
**Action:** Always omit the `href` attribute and add `aria-disabled="true"` alongside `tabindex="-1"` when disabling anchor tags.
