---
name: warn-claude-md-generated-block
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: (^|/)CLAUDE\.md$
  - field: old_text
    operator: regex_match
    pattern: exact:begin|exact:end|bun exact\.mjs|\.exact/checkout
---

⚠️ **This text is in CLAUDE.md's `exact:begin … exact:end` block**, which `bun exact.mjs update` rewrites. Put project notes after `exact:end`.
