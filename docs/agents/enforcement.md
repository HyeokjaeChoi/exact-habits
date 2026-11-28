# Rule-to-check table

Each repo rule and the check that holds it. Add a row when you add a rule.
Prefer a hard check (test, CI, ruleset, `permissions.deny`) to text.
The full reasoning is in [claude-md-plan.md](claude-md-plan.md).

## Mechanisms

| Mechanism | Strength | Reaches the model | Works for other agents |
|---|---|---|---|
| GitHub ruleset `protect-main` | hard, server | at push time | yes |
| CI workflow | hard after it is a required check | in PR checks | yes |
| `bun test` (`rules.test.ts`) | hard in CI, manual locally | test output | yes |
| `bun exact.mjs test web\|macos`, `verify web\|ios\|android` | hard when run; manual | command output | yes |
| `permissions.deny` in `.claude/settings.json` | hard, Claude Code only | denial text | no |
| Path-scoped rule (`.claude/rules/code.md`) | context, not a check | yes, when a matching file is read or edited | by link only |
| hookify `block` | soft: fails open | only "Blocked by hook" | no |
| hookify `warn` | none for the model | no | no |
| AI review (`ai-review.yml`) | advisory, label-triggered | PR comment | yes |
| Inline text in `AGENTS.md` | judgement | yes, each session | yes |

`[src]` hookify fails open. Its hook exits 0 on each error, and it loads rules from `.claude/` relative to the current directory.
`[doc]` "Permission rules are enforced by Claude Code, not by the model."

## Rules

Status: EXISTS, NEW, CHANGED, LATER.

| # | Rule | Mechanism | Status |
|---|---|---|---|
| 1 | Do not edit `exact.mjs`, `app.contract.d.ts`, `.exact/` | hookify `block-generated-files` | EXISTS |
|   |   | `permissions.deny`: three `Edit(...)` rules | NEW |
| 2 | Do not edit the generated block in `AGENTS.md` | hookify `block-exact-block-edit` (Edit) | CHANGED |
|   |   | hookify `block-agents-md-overwrite` (Write) | NEW |
|   |   | `bun test`: block is first, single, and has the pinned SHA-256 | NEW |
| 3 | `AGENTS.md` has 125 lines or fewer | `bun test` | NEW |
| 4 | `CLAUDE.md` has the same content as `AGENTS.md` | `bun test` | NEW |
| 5 | Each link in the index points to a file | `bun test` | NEW |
| 6 | Views use native symbol and colour roles only | `bun test`: lint of `**/*.contract` | NEW |
|   |   | `.claude/rules/code.md` | NEW |
|   |   | hookify `warn-contract-non-native` (human-visible) | CHANGED |
| 7 | Tests pass before a commit | CI `test.yml`: `bun test` | NEW |
|   |   | `bun exact.mjs test web`, `test macos` (manual) | EXISTS |
|   |   | hookify `warn-commit-without-tests` (human-visible) | EXISTS |
|   |   | CI: `bun exact.mjs test web` | LATER |
| 8 | Platform verify at the end of a batch | `bun exact.mjs verify web\|ios\|android` (manual) | EXISTS |
| 9 | Change the seam only when the ticket names it; update `SPEC.md` in the same PR | AI review, criterion 2 | EXISTS |
|   |   | `.claude/rules/code.md` and inline text | NEW |
|   |   | judgement: doc only for "the ticket names it" |   |
| 10 | Keep each testId in `SPEC.md` | `bun exact.mjs test web` (`app.test.contract` taps by testId) | EXISTS |
| 11 | No bare `git stash`, no `git stash pop` | `permissions.deny`: four `Bash(...)` rules | NEW |
| 12 | No push to `main`; a PR is necessary | ruleset `protect-main` (PR, no force push, no deletion, no bypass actor) | EXISTS |
| 13 | Workflow steps 1-5 | judgement: doc only | NEW text |
| 14 | One simulator for each parallel session | judgement: doc only | NEW text |
| 15 | A test does not end with a sheet open | `bun exact.mjs verify ios` reports the a11y tree as unread | EXISTS |
|   |   | `.claude/rules/code.md` | NEW |
| 16 | An image in a route header breaks the macOS header | judgement: doc only (`.claude/rules/code.md`) | NEW text |
| 17 | Think first, keep it simple, surgical changes, verify the goal | judgement: doc only | NEW text |
| 18 | English text uses STE | judgement: doc only | NEW text |
| 19 | Answers to the user are in Korean | user's global `CLAUDE.md`, plus inline text | EXISTS + NEW text |
| 20 | Layer import rules (target architecture) | judgement: doc only now | NEW text |
|   |   | `bun test`: import-boundary test | LATER |
| 21 | The data module does not read the clock | Exact refuses `Date.now` (`SPEC.md`) | EXISTS |

## Ideas not adopted

| Idea | Decision | Reason |
|---|---|---|
| hookify block on `git push … main` | no | The ruleset already rejects the push. A regex cannot see the branch of a bare `git push`. |
| Block `git commit` on `main` | no | hookify sees the command text, not the branch. The ruleset stops the commit at the server. |
| Block `--no-verify` | no | The repo has no git hook. The flag skips nothing. Add the rule together with a git hook. |
| Commit trailer | no | No tool reads a trailer. A squash merge already adds the PR number. |
| hookify warn on `SPEC.md` edits | no | A warn does not reach the model. testId edits are frequent. |
| Native hooks in `settings.json` | no | `permissions.deny` and tests cover the hard rules with less code. |
| `ask` rule `Edit(/AGENTS.md)` | optional | It puts a person in each `AGENTS.md` edit. It also stops headless runs. The owner decides. |
| Git `pre-commit` hook that runs `bun test` | later | It needs `core.hooksPath` in each clone. CI gives the same check with no setup. |
| Seam diff check in CI | later | It needs a parser for seam lines. AI review covers it now. |

