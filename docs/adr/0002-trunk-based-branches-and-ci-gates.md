# ADR-0002: trunk-based branches, release branches for each platform, and CI gates

Status: accepted, 2026-11-28. Not yet applied. `AGENTS.md` still shows the old workflow (`feat/<batch>`).

## Context

- ADR-0001 and PR #27 added local gates. A person can skip a local hook.
- The old workflow used one integration branch for each batch. That branch delayed each merge to `main`.
- The app ships to four platforms: `ios`, `android`, `macos`, `web`. Each platform has its own native check.

## Decision 1: branches

- `main` is the trunk. It is always green and always releasable.
- A ticket branch `feat/<ticket>` opens a PR directly into `main`. There are no batch integration branches.
- A batch is a GitHub milestone. Run `/code-review` over the commit range of the milestone for a batch review.
- A release branch is `release/<platform>/vX.Y`, cut from `main`. Patch versions use the same branch.
- Each platform releases independently.
- Fix `main` first. Then add the label `backport-<platform>`. A workflow opens a cherry-pick PR into that release branch.
- Only the latest version of each platform has support.
- There is no limit on parallel sessions. A PR may stay open for a long time.

Rejected: git-flow and GitHub flow.

## Decision 2: tags and releases

- A tag is `<platform>/vX.Y.Z`. Each platform has its own semver.
- The store build number is the `run_number` of GitHub Actions.
- Only a workflow creates a tag. It creates the tag only when the gates of the release branch head are green.
- The same workflow creates a GitHub Release.

## Decision 3: CI gates

| Gate | When | Checks |
|---|---|---|
| Normal | Each PR | `oxfmt` check, `contract fmt --check`, `oxlint`, `bun test` (with the structure rules in `rules.test.ts`), `bun exact.mjs test web` |
| Release | Each PR into `release/<platform>/**` | Normal, and the native check of that platform only |
| Nightly | Each night on `main` | All native checks. Not required. A failure opens an issue. |

- CI checks out `expo/exact` at the commit in `.exact-commit`. The `pre-push` hook reads the same file.
- CI caches the compiled compiler. The cache key is that commit.
- The gates have no path filters.
- Native checks: `ios` runs `verify ios` with `EXACT_SIM="iPhone 17"`. `android` runs `verify android` on `ubuntu` with a KVM emulator. `macos` runs `test macos` with `EXACT_IDENTITY=-`. `web` runs `verify web`.
- The iPhone Duo check stays manual.
- The jobs use GitHub-hosted runners. The repo is public, so they are free.
- Each release workflow has `workflow_dispatch`.
- A new native job starts as not required. Make it required after 3 green runs in a row.

## Decision 4: rulesets

The owner sets the rulesets. An agent writes the spec only.

| Ruleset | Target | Rules |
|---|---|---|
| `protect-main` | `main` | The normal gates are required. The branch must be up to date. |
| `protect-release` | `release/**` | The normal gates and the native job of the platform are required. PR only. No deletion. |
| `protect-tags` | `*/v*` | Only GitHub Actions creates a tag (bypass). |

## Decision 5: review and the PR template

- The AI review is advice. It is not a required check.
- There is one `.github/pull_request_template.md`: Summary, Evidence, Merge Danger.
- The template has a checklist for `release/**` PRs only:
  - The `ai-review-request` run is done and each finding has an answer.
  - A person did the iPhone Duo check.
  - Screenshots show light mode, dark mode and the largest text size.
  - The PR lists the flags that this release turns on and the flags to remove.

## Decision 6: delivery in this round

This round makes the tag and the GitHub Release only. These are later tickets:

- Web deploy: `web-build`, then a static host.
- Exact OTA: `bun exact.mjs deploy --platform <p> --yes`. It needs a signing key and an origin.
- Store upload: TestFlight and Play internal. It needs credentials as secrets.

## Decision 7: feature flags (pending)

- PostHog supplies the flags and the analytics (`capture`).
- This needs a device-id disclosure, a consent screen and a privacy-label update.
- Callers use one function, `flag(name)`.
- The implementation depends on a spike: `posthog-js-lite` in `app.ts` on web, macOS, iOS and Android. The fallback is a direct REST client with a SQLite cache.
- Write the result of the spike in a new ADR.

## Consequences

- `AGENTS.md` (Workflow) and spec #23 must change: a ticket PR goes into `main`.
- CI needs a checkout of `expo/exact`. The first run compiles the compiler and takes minutes.
- A release for one platform does not wait for the native check of another platform.
