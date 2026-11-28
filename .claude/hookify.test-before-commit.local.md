---
name: warn-commit-without-tests
enabled: true
event: bash
action: warn
pattern: git\s+commit
---

⚠️ **Before committing:** `bun test` and `bun exact.mjs test web` should pass (and `EXACT_IDENTITY=- bun exact.mjs test macos` for view changes). Skip this only if they ran after the last edit.
