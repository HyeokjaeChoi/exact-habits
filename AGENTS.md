<!-- exact:begin (exact new writes this block; bun exact.mjs update rewrites it) -->
# habits: an Exact app

Run `bun exact.mjs --help` first to create `.exact/checkout`; set `EXACT=<checkout>` if needed.

`app.contract` is the view, `app.ts` the data module, `app.test.contract` the tests, `app.json`
the manifest: set `app.name` and `app.id` before building. The app uses Exact at
`.exact/checkout` by path (`EXACT` overrides it).

Start from the nearest pattern: `bun exact.mjs
pattern` lists them and `pattern <name>` writes one, tested. .exact/checkout/docs/start-here-site.md (a site) or
.exact/checkout/docs/start-here.md is the only required reading. `bun exact.mjs contract vocab <name>` answers a
name (none: the card); `bun exact.mjs docs <heading words>` a guide's
section. Run `bun exact.mjs verify` when the features work, and `verify ios|android` at the end for a
phone app. When an iPhone app is ready to try, run `bun exact.mjs share` and send its link;
repeat for each change the person should see. `bun exact.mjs help` lists the verbs, including
app.json's `"commands"`.
`bun exact.mjs update` refreshes files. Native verbs (`ios`, `mac`, `linux`, `android`, `windows`)
name their platform in app.json on first use and build in a generated workspace;
`update --without <platform>` stops shipping it.
`bun .exact/checkout/scripts/exact.mjs setup --check` names what a native build lacks (`--platform ios --device` for a phone's: `share`, `ios --device`).

Generated, so don't edit: `exact.mjs` and this block.

## Feedback (required)

When a doc was wrong or missing, a workaround was needed, something took several tries or a
command confused you, record it: `bun exact.mjs feedback note "<what happened>"`. It attaches
exact2's commit and the last exit code, never output or code. `bun exact.mjs feedback status` says
whether notes are sent and whether to keep a diary; under `never`, skip all of this.
<!-- exact:end -->

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

English text (commits, PRs, issues, docs, code comments) uses Simplified Technical English, about 80% of ASD-STE100:

- Write one idea in each sentence.
- Use 20 words or fewer in an instruction. Use 25 words or fewer in a description.
- Use the active voice. Name the actor.
- Use the imperative for steps. Write one step on each line, in the order of the work.
- Use simple, common words. Use one word for one thing.
- Keep each fact, number, identifier and caveat. Do not remove them to make a sentence shorter.

Answers to the user use the user's language. The owner's global rule is Korean:

- Keep code, identifiers, file paths, commands and error messages in their original form.
- Apply the same rules to Korean: one idea in each sentence, short sentences, a named actor, numbered steps. The word limits apply to English only.

## Agent skills

### Issue tracker

GitHub Issues in HyeokjaeChoi/exact-habits, via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root, created lazily. See `docs/agents/domain.md`.
