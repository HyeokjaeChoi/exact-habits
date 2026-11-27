---
name: warn-contract-non-native
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.contract$
  - field: new_text
    operator: regex_match
    pattern: symbol:sf/|#[0-9a-fA-F]{3,8}\b|rgba?\(
---

⚠️ **Platform-native rule.** Use `symbol:` roles (not `symbol:sf/…`, blank on web and Android) and system colour roles (`-exact-system-<name>`, `-exact-*-label`), not hex or rgb colours.
