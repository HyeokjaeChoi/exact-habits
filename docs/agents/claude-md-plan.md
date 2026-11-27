# Plan: AGENTS.md as an index

Status: APPLIED on branch `chore/claude-tooling`.
Scope: agent instructions for `HyeokjaeChoi/exact-habits`.
Keep this file as the decision record. The live table is [enforcement.md](enforcement.md).

Review changes at apply time:

- This file stays. Apply step 7 (delete) is not done.
- Section 4: the Korean line no longer orders each agent to answer in Korean. It says "use the user's language" and names the owner's Korean rule. Reason: merge danger 6.

Evidence labels in this plan:

- `[doc]`: an official document says it. The URL is in section 5.
- `[run]`: a command in this session showed it.
- `[src]`: local source code shows it.
- `[2nd]`: only secondary sources say it.

## 0. Decisions in short

1. `AGENTS.md` stays the one instruction file. `CLAUDE.md` stays a symlink to it.
2. `AGENTS.md` becomes an index of 116 lines. The generated block stays byte-for-byte.
3. Rules that must always apply stay inline. They are short.
4. File-type rules go to one path-scoped file: `.claude/rules/code.md`.
5. The index points to each detail doc with a plain Markdown link. Other agents can follow a link.
6. Hard checks do the enforcement: `permissions.deny`, `bun test`, CI and the `main` ruleset.
7. hookify stays for two content checks on `AGENTS.md`. hookify is a soft guard.
8. The target architecture goes to `docs/agents/architecture.md`. It is not auto-loaded until the code matches it.

Three findings changed the first design:

- A hookify `warn` rule does not reach the model. `[run]` A Bash command with the text `git commit` matched `warn-commit-without-tests`. No message came back to the agent. `[doc]` The hooks reference calls `systemMessage` a "Warning message shown to the user".
- A hookify `block` rule reaches the model without its message. `[run]` The agent got only `PreToolUse:Write hook error: Blocked by hook`. `[src]` hookify sends no `permissionDecisionReason`.
- Claude Code removes block-level HTML comments from `CLAUDE.md` before it loads the text. `[doc]` Thus the model does not see the `exact:begin` and `exact:end` markers. A visible heading must mark the boundary.

Result: a rule that the model must know goes into loaded text. A rule that must hold goes into a hard check. A hookify `warn` is a note for the human only.

## 1. Target file tree

```text
AGENTS.md                                      CHANGED  index; generated block not touched
CLAUDE.md -> AGENTS.md                         same     symlink
rules.test.ts                                  NEW      repo rules as bun tests
SPEC.md                                        same
.claude/
  settings.json                                CHANGED  adds permissions.deny
  rules/
    code.md                                    NEW      path-scoped: **/*.contract, **/*.ts, SPEC.md
  hookify.claude-md-generated-block.local.md   CHANGED  matches AGENTS.md; action block
  hookify.agents-md-overwrite.local.md         NEW      blocks Write on AGENTS.md
  hookify.contract-native-only.local.md        CHANGED  field content; covers Write
  hookify.generated-files.local.md             same
  hookify.test-before-commit.local.md          same     human-visible note only
.github/workflows/
  test.yml                                     NEW      bun test on each PR and on main
  ai-review.yml                                same
docs/agents/
  architecture.md                              NEW      target state: FSD + UI/domain/data
  enforcement.md                               NEW      rule-to-check table (section 3.2)
  domain.md  issue-tracker.md  triage-labels.md   same
  claude-md-plan.md                            NEW      this plan; delete on apply
```

Not created: `docs/prd/`, `docs/adr/`, `GLOSSARY.md`, a `rules/` folder at the root.
Reason: no content exists for them. Specs are GitHub issues. `docs/agents/domain.md` already says ADRs and the glossary start lazily.

New files: 6, plus this plan. Changed files: 4.

## 2. AGENTS.md outline and line budget

| # | Section | Lines | Content |
|---|---|---|---|
| 1 | Generated Exact block | 32 | Lines 1-31 as they are, then one empty line |
| 2 | `## Project index` | 11 | Boundary sentence. "Read this / Before you" table with 4 links |
| 3 | `## Rules that always apply` | 7 | Generated files, seam, stash, how to edit `AGENTS.md` |
| 4 | `## Commands` | 21 | Environment line, 5 check commands, commit gate, iOS and Android notes |
| 5 | `## Workflow` | 9 | 6 numbered steps from spec issue to PR into `main` |
| 6 | `## How to work` | 7 | 4 principles (section 7.1) |
| 7 | `## Writing style` | 16 | STE rule (section 4) |
| 8 | `## Agent skills` | 13 | As it is now. The setup skill owns this block |
|   | **Total** | **116** | Limit in `rules.test.ts`: 125. Limit in the Claude Code docs: 200 |

Notes:

- `[run]` A scratch copy with this text has 116 lines. All 5 tests in `rules.test.ts` pass on it.
- Text after the block: 84 lines (71 new, 13 as they are now).
- A rough word count found no sentence over 20 words in the new text. `[run]`
- The heading `## Project index` is the visible boundary. Text above it is generated.
- The `## Agent skills` block stays. `[src]` `setup-matt-pocock-skills` looks for that heading and updates the block in place.
- Command notes stay inline. No path rule can load a note when a command runs.
- The full text of sections 2-7 is in Appendix A.

## 3. Rule-to-enforcement table

### 3.1 Mechanisms

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

### 3.2 Table

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

### 3.3 hookify rules

`[src]` Engine facts that the rules use:

- The engine uses `re.search` with `re.IGNORECASE`.
- All conditions must match.
- For Write, `old_text` and `new_text` are empty. Only `content` holds the text.
- `tool_matcher` in the frontmatter limits a rule to named tools.
- The engine reads only `hook_event_name`, `tool_name` and `tool_input`.

`[run]` Each sample below ran through `hooks/pretooluse.py` of hookify 0.1.1. The results are as stated.

#### NEW: `.claude/hookify.agents-md-overwrite.local.md`

```markdown
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
```

Must trigger (result: deny):

```json
{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"/repo/AGENTS.md","content":"# habits\n"}}
```

Must not trigger (result: allow):

```json
{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"/repo/docs/agents/architecture.md","content":"# Architecture\n"}}
```

#### CHANGED: `.claude/hookify.claude-md-generated-block.local.md`

Changes: the path now matches `AGENTS.md`. The action is `block`. The text pattern no longer matches `bun exact.mjs`, because project text also has that command.

`[run]` The current rule does not fire on `AGENTS.md`. Its path pattern matches only `CLAUDE.md`.
`[doc]` Edit and Write refuse to write through a symlink. Thus each real edit names `AGENTS.md`.

```markdown
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
```

Must trigger (result: deny):

```json
{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/repo/AGENTS.md","old_string":"<!-- exact:end -->\n\n## Project index","new_string":"## Project index"}}
```

Must not trigger (result: allow):

```json
{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/repo/AGENTS.md","old_string":"| Web tests | `bun exact.mjs test web` |","new_string":"| Web tests | `bun exact.mjs test web --quiet` |"}}
```

Limit: the pattern is a list of phrases. `[run]` A one-line edit is caught on 10 of the 25 non-empty block lines. The pinned hash in `rules.test.ts` catches each change.
Constraint: hand-written text in `AGENTS.md` must not contain the phrases in the pattern. `[run]` The text in Appendix A contains none.

#### CHANGED: `.claude/hookify.contract-native-only.local.md`

Changes: `new_text` becomes `content`. The hex pattern needs quotes around the colour.

`[run]` The current rule does not fire on Write. For Write, `new_text` is empty.
Reason for the quotes: `#1234` in a comment is an issue number, not a colour.

```markdown
---
name: warn-contract-non-native
enabled: true
event: file
action: warn
conditions:
  - field: file_path
    operator: regex_match
    pattern: \.contract$
  - field: content
    operator: regex_match
    pattern: symbol:sf/|["']#[0-9a-fA-F]{3,8}["']|rgba?\(
---

**Platform-native rule.** Use `symbol:` roles (not `symbol:sf/…`, blank on web and Android) and system colour roles (`-exact-system-<name>`, `-exact-*-label`), not hex or rgb colours. `bun test` fails on these.
```

Must trigger (result: warn):

```json
{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"/repo/pages/today/today.contract","content":"view background-color=\"#ff0000\"\n"}}
```

Must not trigger (result: allow):

```json
{"hook_event_name":"PreToolUse","tool_name":"Edit","tool_input":{"file_path":"/repo/app.contract","old_string":"image \"symbol:add\"","new_string":"image \"symbol:close\" color=\"-exact-system-red\""}}
```

### 3.4 `.claude/settings.json`

Add this key. Keep `enabledPlugins` as it is.

```json
"permissions": {
  "deny": [
    "Edit(/exact.mjs)",
    "Edit(/app.contract.d.ts)",
    "Edit(/.exact/**)",
    "Bash(git stash)",
    "Bash(git stash pop *)",
    "Bash(git stash drop)",
    "Bash(git stash clear)"
  ]
}
```

`[doc]` Facts:

- `Edit` rules apply to all built-in tools that edit files.
- `/path` in project settings starts at the primary working directory. In a worktree session, that is the worktree.
- A Bash rule with no `*` matches one exact command. A final ` *` also matches the bare command.
- Deny rules apply to each subcommand of a compound command.
- A Bash rule is not a security boundary. `git -C . stash` is not matched.

Allowed after the change: `git stash push -u -m <tag>`, `git stash list`, `git stash apply <sha>`, `git stash drop stash@{n}`.
Not tested in this session: this task could not edit `settings.json`. The syntax comes from the docs.

### 3.5 `rules.test.ts`

`[run]` This file passes on the proposed `AGENTS.md`. Each test fails on a matching bad input.

```ts
import { expect, test } from 'bun:test';
import { existsSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';

// Repo rules as tests. The rule-to-check table is docs/agents/enforcement.md.
const at = (path: string) => resolve(import.meta.dir, path);
const agents = readFileSync(at('AGENTS.md'), 'utf8');
const BEGIN = '<!-- exact:begin', END = '<!-- exact:end -->';
// Replace this hash only after `bun exact.mjs update` rewrote the block.
const BLOCK_SHA256 = 'ba896af1cc682381c6a48afaaf2e0ccb6ec764fc6bb9b2f1765b8bdd11cc9e93';

test('AGENTS.md stays a short index (Claude Code docs: under 200 lines)', () => {
  expect(agents.trimEnd().split('\n').length).toBeLessThanOrEqual(125);
});

test('CLAUDE.md has the same content as AGENTS.md', () => {
  expect(readFileSync(at('CLAUDE.md'), 'utf8')).toBe(agents);
});

test('the Exact block is first, single and unchanged', () => {
  expect(agents.startsWith(BEGIN)).toBe(true);
  expect(agents.split(BEGIN).length).toBe(2);
  expect(agents.split(END).length).toBe(2);
  const block = agents.slice(0, agents.indexOf(END) + END.length);
  expect(new Bun.CryptoHasher('sha256').update(block).digest('hex')).toBe(BLOCK_SHA256);
});

test('each link in the index points to a file', () => {
  const index = agents.slice(agents.indexOf(END));
  const dead = [...index.matchAll(/\]\((?!https?:)([^)#]+)/g)].map(m => m[1]).filter(path => !existsSync(at(path)));
  expect(dead).toEqual([]);
});

test('.contract files use native symbol and colour roles only', () => {
  const bad: string[] = [];
  for (const file of new Bun.Glob('**/*.contract').scanSync(import.meta.dir))
    readFileSync(at(file), 'utf8').split('\n').forEach((line, i) => {
      if (/symbol:sf\/|["']#[0-9a-fA-F]{3,8}["']|rgba?\(/.test(line)) bad.push(`${file}:${i + 1}`);
    });
  expect(bad).toEqual([]);
});
```

Why the tests check structure and a hash:

- `[src]` `bun exact.mjs update` finds the block by the two markers. If a marker is damaged, `update` appends a second block.
- The hash is the SHA-256 of the current block (lines 1-31). `[run]`
- `update` can change the block. Then the test fails, and a person replaces the hash. That step is the acknowledgement.

### 3.6 CI: `.github/workflows/test.yml`

```yaml
name: test
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  unit:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v6
      - uses: oven-sh/setup-bun@v2
        with:
          bun-version: 1.4.2
      - run: bun test
```

Feasibility:

- `[run]` `bun test` passes in a clean export of `HEAD` with no `.exact/` and no `app.contract.d.ts`: 16 tests, 44 ms.
- `[src]` Exact's own CI installs Bun 1.4.2 with `oven-sh/setup-bun@v2`.
- `bun exact.mjs test web` in CI is a follow-up, not part of this plan. Reasons:
  - `[src]` `exact.mjs` does not fetch Exact. It links `.exact/checkout` to a local checkout at `../../exact`, or to `EXACT=<path>`.
  - The workflow must clone `expo/exact` (public) itself. This repo pins no Exact commit.
  - `[src]` Exact documents the steps ("Web CI preparation" in its `docs/reference.md`). Prebuilt tools download only when the checkout pins a producer key. If not, the job builds with Rust.
  - Not run in this session. Do a spike on a throwaway branch first.

### 3.7 Ideas not adopted

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

## 4. Response-style rule (exact wording)

This text goes into `AGENTS.md` under `## Writing style`:

```markdown
English text (commits, PRs, issues, docs, code comments) uses Simplified Technical English, about 80% of ASD-STE100:

- Write one idea in each sentence.
- Use 20 words or fewer in an instruction. Use 25 words or fewer in a description.
- Use the active voice. Name the actor.
- Use the imperative for steps. Write one step on each line, in the order of the work.
- Use simple, common words. Use one word for one thing.
- Keep each fact, number, identifier and caveat. Do not remove them to make a sentence shorter.

Answers to the user:

- Answer in Korean. Keep code, identifiers, file paths, commands and error messages in their original form.
- Apply the same rules to Korean: one idea in each sentence, short sentences, a named actor, numbered steps. The word limits apply to English only.
```

Why this wording:

- The rule states each STE rule as a concrete instruction. `[doc]` Claude Code docs: write instructions "concrete enough to verify".
- The rule names ASD-STE100 once. The model knows the standard, and the name gives the full style.
- "About 80%" means: keep the structure rules, and do not use the approved-word dictionary. This follows Karpathy's "80% of the way to ASD-STE100". `[2nd]`
- The "Keep each fact" line is a guard. `[2nd]` One small test reports that the formal standard made Claude drop 46.8% of code facts. A looser instruction lost 8.5%.
- The Korean line repeats the owner's global rule. It adds the sentence rules. STE word counts do not fit Korean.
- No mechanical check exists for this rule. It is "judgement: doc only".

## 5. Sources

Claude Code:

- Memory, rules, imports, AGENTS.md, size, HTML comments, `/compact`: https://code.claude.com/docs/en/memory
- When `.claude/rules/` files load: https://code.claude.com/docs/en/claude-directory
- Hook output fields (`systemMessage`, `permissionDecisionReason`, `additionalContext`): https://code.claude.com/docs/en/hooks
- Permission rules: https://code.claude.com/docs/en/permissions
- hookify 0.1.1 source: `~/.claude/plugins/cache/claude-plugins-official/hookify/0.1.1/` (`core/rule_engine.py`, `core/config_loader.py`, `hooks/pretooluse.py`)

Karpathy skills:

- Repo and `CLAUDE.md`: https://github.com/multica-ai/andrej-karpathy-skills
- The post that the README cites (not opened; x.com returned HTTP 402): https://x.com/karpathy/status/2015883857489522876
- Secondary account of that post: https://dev.to/ramunarasinga-11/andrej-karpathy-skills-a-single-claudemd-file-to-improve-claude-code-behavior-7jb

STE:

- The post on ASD-STE100 (not opened; x.com returned HTTP 402): https://x.com/karpathy/status/2105819303471976479
- Hacker News submission of that post, and a comment with its full text: https://news.ycombinator.com/item?id=50102315 and https://news.ycombinator.com/item?id=50102322
- Blog post that links and dates it (2026-10-02): https://kgolubic.com/posts/asd-ste100-and-llms/
- Skills that cite it: https://github.com/Dodaios/ste80-humanizer and https://github.com/ajithraghavan/make-it-click
- Earlier STE skill on Hacker News (2026-07-30): https://news.ycombinator.com/item?id=49114639
- Summary of the fact-loss test by Lucian Ghinda: https://daily.dev/posts/explain-to-me-in-simple-technical-english-jcs3quoze
- STE rules, Issue 9 (January 2025), 53 writing rules, about 900 words: https://en.wikipedia.org/wiki/Simplified_Technical_English

Other:

- AGENTS.md format ("just standard Markdown", no import syntax): https://agents.md/
- FSD layers and the import rule: https://feature-sliced.design/docs/reference/layers
- Android app architecture guide: https://developer.android.com/topic/architecture
- Exact (public): https://github.com/expo/exact (`game/new.mjs` for the block, `docs/reference.md` for "Web CI preparation")
- Ruleset: `gh api repos/HyeokjaeChoi/exact-habits/rulesets/28241585`

## 6. Merge danger

This section is about the PR that applies the plan. The plan file alone changes no behaviour.

1. **Blocked writes to `AGENTS.md`.** Each Write to any `AGENTS.md` or `CLAUDE.md` is blocked, in any folder. `/init`, `claude-md-management` and `setup-matt-pocock-skills` must use Edit.
2. **Opaque blocks.** The agent sees only "Blocked by hook". The inline rules must explain the cause. Do not remove them.
3. **Phrase collisions.** An Edit of `AGENTS.md` is blocked if `old_string` has a phrase from the pattern in 3.3. Keep those phrases out of hand-written text.
4. **Pinned hash.** After `bun exact.mjs update` changes the block, `bun test` fails until a person replaces the hash. A branch that ran `update` fails CI.
5. **Stash deny.** Claude sessions cannot run `git stash`, `git stash pop`, bare `git stash drop` or `git stash clear`. A session that depends on them stops with a denial.
6. **All agents get the new rules.** The CI reviewer and Codex read the same file. "Answer in Korean" and the STE rule now apply to them also.
7. **Commit text.** The STE rule can conflict with the commit rules that Claude Code adds by itself. `[doc]` The docs name `includeGitInstructions` for this case.
8. **Native-only becomes hard.** Today it is a warning. After the merge, a hex colour in a `.contract` file fails `bun test` and CI.
9. **Mixed worktrees.** `.claude/` is checked in. A worktree on an old branch keeps the old rules until it merges `main`.
10. **Subfolder sessions.** hookify loads rules relative to the current directory. A session that starts in a subfolder has no hookify rules. The hard checks still hold.
11. **New CI job.** `test` runs on each PR. It is not a required check, so it cannot stop a merge yet.
12. **Public repo.** The repo is public. Each line in `AGENTS.md` is public.
13. **Conflicts.** A branch that edited `AGENTS.md` after line 31 gets a merge conflict.

## 7. Research results

### 7.1 Karpathy skills (research A)

- The file is not Karpathy's own. Jiayuan Zhang (GitHub `forrestchang`) wrote it. `[run]` The first commit is from 2026-01-27 by him.
- The repo is now `multica-ai/andrej-karpathy-skills`. `forrestchang/andrej-karpathy-skills` redirects to it. `[run]`
- The README says the file is "derived from" a Karpathy post on LLM coding pitfalls. It quotes the post. `[2nd]` The post date is 2026-01-26.
- The file has four principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution.
- `[run]` The GitHub API reports no license. This plan uses the four ideas in new words. It copies no text.

Adapted text for `## How to work`:

```markdown
- Think first. State your assumptions. If the ticket is not clear, ask before you write code.
- Keep it simple. Write the minimum code for the ticket. Add no feature, option or abstraction that the ticket does not name.
- Make surgical changes. Do not refactor, reformat or delete code that the ticket does not name. Remove only what your change made unused.
- Verify the goal. Name the check first. Work until the check passes. Do not report "done" before the commands above pass.
```

What changed for this repo: "the request" became "the ticket". "Success criteria" became the commands in `## Commands`.

### 7.2 STE claim (research B)

Claim: Karpathy recommended STE for how agents answer.
Result: supported by secondary sources, with a narrower meaning.

- `[2nd]` Three separate sources give the same post ID and the date 2026-10-02. Two of them quote the same text.
- The text says: ask the LLM to explain something in ASD-STE100. He sometimes asks for "80% of the way to ASD-STE100", because the spec is strict.
- The tip is about explanations that a person reads. It is one of four tips: writing, diagrams, HTML pages, explainer videos.
- The post does not name commit messages, PR bodies or code comments. That use is this repo's decision.
- The primary post was not opened. x.com returned HTTP 402 in this session.
- The idea is older than the post. An STE skill for agents was on Hacker News on 2026-07-30.

### 7.3 Loading mechanism (research C)

| Option | When it loads `[doc]` | Context cost | Other agents | Decision |
|---|---|---|---|---|
| Inline in `AGENTS.md` | Each session. Loaded again after `/compact` | always | read it | Use for rules that always apply |
| `@path` import | At launch, with the file that imports it | same as inline | see the literal text | Do not use |
| `.claude/rules/*.md`, no `paths:` | At launch | always | do not load it | Do not use |
| `.claude/rules/*.md` with `paths:` | When Claude reads, writes or edits a matching file | on demand | follow a link to it | Use for file-type rules |
| Plain link in the index | When the model opens the file | on demand | follow it | Use for task docs |

Answers to the four questions, all `[doc]`:

1. Rules with no `paths:` load at launch, with the same priority as `.claude/CLAUDE.md`.
2. A path-scoped rule loads when Claude uses Read, Write or Edit on a matching file. `cat` or `head` on one file also counts.
3. Imports load at launch with the importing file. They "don't reduce its context cost". The depth limit is four hops.
4. Claude Code reads `AGENTS.md` natively from v2.1.277, but only when no `CLAUDE.md` exists at or above the working directory. With the symlink, Claude reads the content once, as `CLAUDE.md`.

Other facts that the plan uses, all `[doc]`:

- Target under 200 lines for each `CLAUDE.md`. Longer files "reduce adherence".
- `CLAUDE.md` content arrives as a user message. Compliance is not guaranteed.
- A path-scoped rule loads again only on the next matching file after `/compact`. The root `CLAUDE.md` loads again at once.
- For a rule that "must run at a specific point", the docs say to use a hook.

Why keep the symlink and not `@AGENTS.md`:

- `[src]` Exact creates the symlink. `update` treats a `CLAUDE.md` that is a normal file as a copy, and appends the generated block to it.
- `[doc]` With a symlink, Edit and Write send the agent to `AGENTS.md`.

Why the rule file is in `.claude/rules/` and the index links to it:

- Claude Code loads it by itself at the right time. That does not depend on the model.
- Another agent reads `AGENTS.md`, sees the link, and opens the same file. There is one copy of each rule.
- Alternative: keep the file in `docs/agents/` and symlink it into `.claude/rules/`. `[doc]` Symlinks there are supported. This adds one link for each file.

## 8. Architecture rule (target state)

This is the text for `docs/agents/architecture.md`.

```markdown
# Architecture (target state, not yet applied)

Status: TARGET. The code is still flat: `app.contract`, `app.ts`, `streak.ts`.
Do not move a file unless the ticket is the restructure ticket.

## Views: Feature-Sliced Design

`app.contract` stays at the root. It holds the routes and the root component.
Split the other view code into files. Import them with `use X from "./file.contract"`.

| Layer, high to low | Folder | Holds |
|---|---|---|
| app | `app.contract` | Routes, root component |
| pages | `pages/<page>/` | One screen for each route |
| widgets | `widgets/<widget>/` | A large UI block that two or more pages use |
| features | `features/<feature>/` | One user action, for example "add a habit" |
| entities | `entities/<entity>/` | The view of one business object, for example a habit |
| shared | `shared/` | UI parts and `fn`s with no business meaning |

Rules:

1. A file imports only from a layer below its own layer.
2. A slice does not import another slice on the same layer.
3. `shared/` imports from no other layer.
4. Make a layer folder only when a file goes into it.
5. The seam in `SPEC.md` does not change in the restructure.

## TypeScript: UI, domain and data layers

| Layer | Place | Holds |
|---|---|---|
| UI | `*.contract` | Views. They call sources through the seam. They import no TypeScript. |
| entry | `app.ts` | `answer` and `grants`. Exact loads this file. |
| domain | `domain/` | Pure logic: streak math, calendar days. |
| data | `data/` | SQLite: schema, migration, queries. |

Rules:

1. The call direction is UI, then domain, then data.
2. `domain/` is pure. It does not open SQLite, read the clock, or import `data/` or `app.ts`.
3. Only `data/` contains SQL.
4. A unit test sits next to its file: `domain/streak.test.ts`.

Open decision (write ADR-0001 in the restructure ticket):
Rule 1 and rule 2 conflict if domain code imports data code.

- Option A: a domain function takes the data functions as arguments. `app.ts` connects them.
- Option B: `data/` imports `domain/`. The code does this today (`app.ts` imports `streak.ts`).

## Mechanical checks to add with the restructure

Add these to `rules.test.ts` in the restructure PR:

1. Read each `use … from "./…contract"` line. Fail if the import goes up, or across slices on one layer.
2. Read each `import` in `domain/**`. Fail if the path leaves `domain/`.
3. Fail if a file outside `data/` contains SQL keywords in a string.

After the restructure PR merges, move the rules into `.claude/rules/` with `paths:` for each folder.
```

Source notes:

- `[doc]` FSD: "A module (file) in a slice can only import other slices when they are located on layers strictly below."
- `[doc]` Android guide: the domain layer is optional and "depends on data layer classes". The guide puts business logic in the data layer.
- The owner's wording is "UI → domain → data, domain pure". A pure domain cannot import data. That is the open decision.
- Why not auto-load this doc now: `[doc]` outdated or conflicting instructions reduce adherence. A target rule conflicts with flat code.

## 9. Apply steps

1. Add `rules.test.ts`. Run `bun test`. It must pass on the current `AGENTS.md`.
2. Add `docs/agents/architecture.md`, `docs/agents/enforcement.md` and `.claude/rules/code.md`.
3. Insert Appendix A into `AGENTS.md` between line 32 and `## Agent skills`. Use Edit.
4. Change the two hookify files. Add the new hookify file.
5. Add `permissions.deny` to `.claude/settings.json`.
6. Add `.github/workflows/test.yml`.
7. Delete this plan file.
8. Run `bun test`. Then run the six samples in 3.3 through the hookify engine.
9. Start a new session. Run `/context all`. Confirm `CLAUDE.md` is under "Memory files".
10. Read `app.contract` in that session. Confirm that `.claude/rules/code.md` loads.
11. Run `/permissions`. Confirm the seven deny rules.
12. Optional: run `/doctor prompt-audit` to find conflicts. `[doc]` It needs v2.1.283 or later.


Follow-ups, each in its own ticket:

- F1. Spike: `bun exact.mjs test web` in CI, with a pinned Exact commit.
- F2. Make the `unit` job a required check in `protect-main`. Do this after the job is stable.
- F3. Restructure PR: ADR-0001, import-boundary tests, path-scoped layer rules.
- F4. Add `docs/agents/architecture.md` to the context list in the `ai-review.yml` prompt.
- F5. Decide on `includeGitInstructions` if commit text does not follow the STE rule.

## 10. Uncertain points

1. The two X posts were not opened. Their text comes from secondary quotes.
2. The `permissions.deny` rules were not run. Only the docs support the syntax.
3. "Blocked by hook" with no message was seen in one session, in one client. Other versions can differ.
4. The `warn` result is one observation plus the docs. No test proves it for each client.
5. Is native-only an absolute rule? The plan makes it a failing test. If exceptions exist, remove test 5 and keep the warning.
6. The meaning of "(FR / NFR / HLD / LLD / acceptance)" is not clear: sections of one ticket, or kinds of tickets. The plan keeps the words.
7. "Answer in Korean" in a checked-in file applies to each agent and each contributor. The owner can limit it to the global file.
8. `bun exact.mjs test web` in CI was not run. The Exact docs say it is possible.
9. The fact-loss numbers for STE come from one small test, read second-hand.
10. The line limit 125 is a choice. The docs limit is 200.

## Appendix A: hand-written text for `AGENTS.md`

Insert after line 32 (the empty line after the `exact:end` marker). Keep `## Agent skills` after it.

````markdown
## Project index

This file is an index. Exact generates all text above this heading. Do not edit that text.

| Read this | Before you |
|---|---|
| [SPEC.md](SPEC.md) | change a screen, a testId, a source or the seam |
| [.claude/rules/code.md](.claude/rules/code.md) | edit a `.contract` or `.ts` file (Claude Code loads it by itself) |
| [docs/agents/architecture.md](docs/agents/architecture.md) | add or move a file or a folder |
| [docs/agents/enforcement.md](docs/agents/enforcement.md) | add or change a rule or its check |

## Rules that always apply

- Do not edit generated files: `exact.mjs`, `app.contract.d.ts`, `.exact/`. Change `app.contract` or `app.ts`, or run `bun exact.mjs update`.
- Change the seam only when the ticket names it. The seam is the shapes, the source names and the source arguments in `SPEC.md`. Update `SPEC.md` in the same PR.
- Do not run `git stash` without `-m <tag>`. Do not run `git stash pop`. All worktrees share one stash. Make a WIP commit instead.
- Change `AGENTS.md` with small edits below this index heading. Do not write the full file again. `CLAUDE.md` is a link to `AGENTS.md`.

## Commands

Set the environment first:

```sh
export PATH="$HOME/.bun-1.4.2/bin:$HOME/.cargo/bin:$PATH" EXACT_FEEDBACK=0
```

| Check | Command |
|---|---|
| Unit tests and repo rules | `bun test` |
| Web tests | `bun exact.mjs test web` |
| macOS tests | `EXACT_IDENTITY=- bun exact.mjs test macos` |
| iOS | `EXACT_SIM="<iPhone>" bun exact.mjs verify ios` |
| Android | `ANDROID_SERIAL=emulator-5554 bun exact.mjs verify android` |

- Before each commit, `bun test` and `bun exact.mjs test web` must pass. After a view change, the macOS tests must pass also.
- iOS: use one simulator for each parallel session. Shut the simulator down after the run.
- iOS: the iPhone Duo leg cannot tap header bar buttons (`habit-menu`). This is a known Exact agent gap. "drive busy" means that another session holds the Duo. Try again later.
- Android: the AVD is `habits_api37`. Mirror it with `android device hub`.

## Workflow

1. Write one spec issue.
2. Split the spec into ticket issues (FR, NFR, HLD, LLD, acceptance).
3. Use one worktree and one session for each ticket.
4. Open each ticket PR into `feat/<batch>`.
5. Run the integration verify on `feat/<batch>`. Then run `/code-review`.
6. Open one PR from `feat/<batch>` into `main`. The `main` ruleset requires a PR.

## How to work

- Think first. State your assumptions. If the ticket is not clear, ask before you write code.
- Keep it simple. Write the minimum code for the ticket. Add no feature, option or abstraction that the ticket does not name.
- Make surgical changes. Do not refactor, reformat or delete code that the ticket does not name. Remove only what your change made unused.
- Verify the goal. Name the check first. Work until the check passes. Do not report "done" before the commands above pass.

## Writing style

(The text in section 4.)
````

Where each approved line went:

| Approved content | Place |
|---|---|
| Environment line, three test commands | `## Commands`, inline |
| `verify ios` simulator rule, Duo gap, "drive busy" | `## Commands`, inline |
| `verify android`, AVD, mirror | `## Commands`, inline |
| Workflow chain | `## Workflow`, inline, as 6 steps |
| Sheet open at the end of a test | `.claude/rules/code.md` |
| Image in a route header on macOS | `.claude/rules/code.md` |
| Seam rule | `## Rules that always apply`, and `.claude/rules/code.md` |

## Appendix B: `.claude/rules/code.md`

```markdown
---
paths:
  - "**/*.contract"
  - "**/*.ts"
  - "SPEC.md"
---

# Code rules

These rules describe the code as it is now. The target layout is in `docs/agents/architecture.md`.

## Seam

- `SPEC.md` holds the seam and the testIds. Read it before you change a view, a test or a source.
- Change the seam only when the ticket names it. Update `SPEC.md` in the same PR.
- `app.ts` exports only `answer` and `grants`.

## Views (`*.contract`)

- Use `symbol:` roles. Do not use `symbol:sf/…`. Those symbols are blank on web and Android.
- Use system colour roles: `-exact-system-<name>`, `-exact-*-label`. Do not use hex or rgb colours.
- An image in a route header makes macOS draw the whole header in the page (`header-item-left-out`).
- Keep each testId that `SPEC.md` lists.

## Tests (`app.test.contract`)

- Do not end a test with a sheet open. End with `tap "add-cancel"`.
- If a sheet stays open, `verify ios` reports the a11y tree as unread.

## Data (`app.ts`, `streak.ts`)

- `streak.ts` is pure. It does not open SQLite, read the clock or import `app.ts`.
- The data module does not read the clock. "today" comes as an argument. See `SPEC.md`.
```

Each line comes from the approved content, an existing hookify rule, `SPEC.md` or the code. The plan adds no new coding rule.
