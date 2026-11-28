---
name: block-exact-block-edit
enabled: true
event: file
action: block
conditions:
  - field: file_path
    operator: regex_match
    pattern: (^|/)(AGENTS|CLAUDE)\.md$
  - field: old_text
    operator: regex_match
    pattern: exact:(begin|end)|an Exact app|start-here|contract vocab|feedback (note|status)|setup --check|update --without|EXACT=<checkout>
---

**Generated block.** `bun exact.mjs update` rewrites the text from `exact:begin` to `exact:end` in AGENTS.md. Do not edit that text. Add project text below the `## Project index` heading.
