---
name: warn-commit-without-tests
enabled: true
event: bash
action: warn
pattern: git\s+commit
---

⚠️ **Before committing:** the `pre-commit` hook runs `scripts/gate.sh fast`. `bun exact.mjs test web` runs in the `pre-push` hook. After a view change, run `EXACT_IDENTITY=- bun exact.mjs test macos` also.
