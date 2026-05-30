## 2025-05-30 - Focus-visible styles on custom dark themes
**Learning:** Custom styled buttons and inputs on dark themes often lose default browser outline focus styles. Setting focus without 'focus-visible' breaks keyboard accessibility. Links dynamically generated need aria-labels.
**Action:** Always verify custom controls have explicit :focus-visible states and dynamically generated interactive elements have descriptive ARIA labels.
