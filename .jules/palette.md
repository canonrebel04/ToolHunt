## YYYY-MM-DD - [Keyboard Accessibility for Disabled Links]
**Learning:** Keyboard users can accidentally focus on disabled <a> tags if they have an href attribute like href="#", causing unwanted navigation. pointer-events: none also hides the disabled state from mouse users.
**Action:** Use conditional rendering to omit the href attribute entirely for disabled links and apply role="button" with aria-disabled="true". Use cursor: not-allowed instead of pointer-events: none to give clear visual feedback.
