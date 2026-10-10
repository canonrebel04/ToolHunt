## YYYY-MM-DD - [Added Disabled States for Async Operations]
**Learning:** Found that the primary search functionality lacked disabled states during asynchronous operations, which could lead to redundant API calls and user confusion.
**Action:** Always implement `disabled` state with visual opacity and a loading spinner for async submit buttons to provide immediate, accessible feedback and prevent double submissions.
## YYYY-MM-DD - [Improved Disabled Links and Icon Accessibility]
**Learning:** Found that \`pointer-events: none\` on disabled links hides them from mouse users but leaves them in the keyboard tab sequence, causing screen readers to focus on broken links. Also noted decorative FontAwesome icons lack \`aria-hidden="true"\`, causing redundant announcements.
**Action:** Use \`cursor: not-allowed\`, \`aria-disabled="true"\`, \`tabindex="-1"\`, and \`onclick="return false;"\` for disabled links to ensure full keyboard/screen reader accessibility while preserving hover cues. Always add \`aria-hidden="true"\` to purely decorative \`<i>\` tags.
