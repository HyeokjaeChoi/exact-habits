---
name: block-generated-files
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: (^|/)(exact\.mjs|app\.contract\.d\.ts)$|(^|/)\.exact/
---

🛑 **Generated file.** `exact.mjs`, `app.contract.d.ts` and `.exact/` are written by Exact. Change `app.contract` / `app.ts` instead, or run `bun exact.mjs update`.
