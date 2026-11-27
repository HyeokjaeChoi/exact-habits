# Review guide

The AI reviewer (`.github/workflows/ai-review.yml`, label `ai-review-request`) and people read this before reviewing a PR.
CI reads this file from the PR base branch, so a PR that changes a rule is reviewed against the old rule.

A review answers three questions, in this order:

1. **Requirements.** What does the PR claim to implement (linked issue, PR description, the SPEC.md sections it touches)?
   Check each requirement against the code and the tests: met, partial, gap, or not checkable here.
2. **History.** Does it reverse an earlier decision, bring back a fixed bug, or ignore a concern raised on an earlier PR?
   Read the log and the review threads of the files it changes.
3. **Fit.** Does it belong in the codebase: owner file, seam, existing helpers, patterns, all four platforms?

Read beyond the diff: callers, callees and tests of each changed symbol. Report a bug only with a concrete failure scenario.

## What to read

| Changed path | Also read |
|---|---|
| `app.contract` | [SPEC.md](SPEC.md) "Seam (do not change)" and "Screens and testIds"; the actions and `fn`s the view calls; `app.test.contract` for the `testId`s it must keep. |
| `app.ts`, `streak.ts` | [SPEC.md](SPEC.md) "Streak rules" and the data seam table; `streak.test.ts`. |
| `streak.test.ts`, `app.test.contract` | The behaviour they pin in [SPEC.md](SPEC.md); a test that changes to match new code needs the spec to change too. |
| `SPEC.md`, `AGENTS.md`, `docs/` | The code they describe. Code and spec must agree after the PR. |
| `.github/`, `REVIEW.md` | [Evals](#evals): a change to the review itself is measured, not trusted. |

## Rules that matter most here

- The seam in [SPEC.md](SPEC.md) does not change: `routes`, `shape`s, `fn`s, `resource` and `mutation` lines, and the actions `step`, `back`, `follow`, `openAdd`, `editName`, `save`, `afterSave`, `toggle`, `askRemove`, `remove`.
- Owners: UI in `app.contract`; data and streak math in `app.ts`, `streak.ts`; tests in `streak.test.ts` and `app.test.contract`.
- The data module never reads the clock; "today" arrives as an argument. Day arithmetic is calendar arithmetic on the `YYYY-MM-DD` key, never `ms ± 86400000` on local time.
- Streak rules, uniqueness (case-insensitive habit names), idempotent `setDone`, and `removeHabit` deleting check-ins are specified in SPEC.md; a change to any of them needs the spec and its tests to change in the same PR.

## Do not flag

- Style, naming taste, formatting.
- Anything a type check or an existing test already catches and fails on.
- Code the PR does not touch, unless the PR makes it worse.
- `.github/review/evals/`: fixtures with seeded bugs on purpose. Review a change there as an eval case (does the patch apply, does `expected` describe the defect), not as app code.

## Output

Each finding has a severity: **Critical** (data loss, security, crash on startup), **Major** (wrong result on a reachable input, an unmet requirement, a broken seam), **Minor** (a real but small problem). It gives the failure scenario, the evidence (`path:line`) and its source (SPEC.md section, issue, commit or PR). A second pass tries to refute every finding; only confirmed findings are posted inline.

## Lessons

Rules learned from past reviews. The weekly learning job (`.github/workflows/ai-review-learn.yml`) proposes changes here from how people answered the AI's findings. A person reviews and merges them; add the `ai-review-eval-request` label to the proposal first to check that the eval does not get worse.
Format: `- L<n> (<category>): <rule in one or two sentences>. Evidence: PR #<a>, #<b>.`

<!-- lessons:begin -->
<!-- No lessons yet. -->
<!-- lessons:end -->

## Learning loop and evals

1. **In every review**: a reviewer pass finds candidates; a verifier pass with fresh context tries to refute each one. Only confirmed findings are posted; unconfirmed ones are listed for a person to look at.
2. **After merges**: each inline finding carries a hidden marker. Every Monday the learning job reads how people answered the findings from the last 30 days (resolved, outdated, 👍, 👎, replies) and human review comments the AI missed, shows the precision numbers in the run summary, and opens a PR that edits the Lessons section.
3. **Evals**: `.github/review/evals/cases/` holds seeded changes against a pinned commit of this repo (bugs the reviewer must catch, clean changes it must leave alone). The label `ai-review-eval-request` on a PR (or a manual run) replays them with the PR's review configuration, scores recall, precision and false positives with a judge model, and compares them with `evals/thresholds.json` and `evals/baseline.json`. Change the prompts, this file or `config.json` only with a passing eval, and update `baseline.json` in the same PR.
4. **A miss or a false positive found in real use** becomes a new eval case: add `cases/<id>/case.json` and `change.patch` (see an existing case), so the same mistake is measured from then on.
