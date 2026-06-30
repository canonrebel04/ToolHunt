## 2026-06-30 - Add missing accessibility attributes to visually disabled UI elements
**Learning:** When visually disabling UI elements like anchor tags (`<a>`) using CSS (e.g., `pointer-events: none; opacity: 0.5;`), they remain accessible to keyboard navigation and screen readers as active links, resulting in a confusing 'ghost' link state.
**Action:** Always include `tabindex="-1"` to prevent keyboard focus and `aria-disabled="true"` to explicitly convey the disabled state to assistive technologies when visually disabling interactive elements.
