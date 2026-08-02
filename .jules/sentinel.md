
## 2025-02-23 - Overreaching Lint Formatting
**Vulnerability:** Global auto-formatting can strip test suppression comments and cause CI pipelines to fail if bounded constraints (e.g. 50 lines max) are strict.
**Learning:** Broad tools like `ruff check . --fix` blindly modify files you aren't intending to touch, causing unrelated regressions or failing CI jobs due to unexpected changes like deleting `# noqa: F811` that tests relied on.
**Prevention:** Fix linter errors explicitly using targeted file paths and targeted rules, prioritizing minimal manual adjustments over global scripts.
