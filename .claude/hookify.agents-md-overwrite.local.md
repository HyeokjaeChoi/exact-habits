---
name: block-agents-md-overwrite
enabled: true
event: file
action: block
tool_matcher: Write
conditions:
  - field: file_path
    operator: regex_match
    pattern: (^|/)(AGENTS|CLAUDE)\.md$
---

**Do not write the full file.** A full write can damage the generated Exact block in AGENTS.md. Use Edit. Change only text below the `## Project index` heading.
