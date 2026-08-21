## 2026-08-21 - Dynamic Link Accessibility
**Learning:** Rendering unavailable dynamic links with just opacity and pointer-events is insufficient for accessibility, as screen readers still try to interact with them and the link lacks clear context.
**Action:** Use `aria-disabled="true"`, `tabindex="-1"`, and context-specific `aria-label` (e.g., 'Access Tool Name') for dynamically generated links that are disabled.
