# ADR-0001: `HabitDb` interface, and Feature-Sliced Design with pages first

Status: accepted, 2026-11-28. Not yet applied. The code is still flat.

## Context

- Each UI ticket edits the one file `app.contract`. Parallel worktree sessions collide there.
- `app.ts` mixes SQL with the call to the pure streak rules. A unit test of a source needs SQLite.
- The owner wants unit tests that use a fake of the storage.

## Decision 1: the data module uses a `HabitDb` interface

- `model/` holds the pure rules and the `HabitDb` interface. `model/` imports nothing outside `model/`.
- `db/` holds the SQLite implementation of `HabitDb`, the schema and the migration.
- `app.ts` builds the SQLite `HabitDb` and passes it to the `model/` functions. `app.ts` is the only file that imports both.
- The import direction is `app.ts`, then `db/`, then `model/`.
- A `model/` function takes a `HabitDb` as its first argument. Do not write classes or use a DI library.
- `fakeHabitDb()` is an in-memory `HabitDb` for unit tests.
- One test suite runs against the fake and against the SQLite implementation. If `bun test` cannot open the SQLite handle, the web tests cover SQLite. Record that in the PR.
- The interface has no schema or migration method.
- Do not add a `Clock` interface. "today" stays an argument.
- Do not use the words `store` or `storage` for these files. Exact uses them as argument names of `answer`.

Rejected: `db/` code calls the pure functions directly, with no interface. That is less code, but a unit test of a source then needs SQLite.

## Decision 2: views follow Feature-Sliced Design v2.1, pages first

- Start with three layers: `app.contract` (the app layer), `pages/`, `shared/`.
- Put code in its page first. Add `features/` or `entities/` only when all three conditions are true:
  1. Two or more places use the same code now.
  2. The code has a reason to change that does not depend on one user of it.
  3. The boundary has one responsibility.
- Do not add `widgets/`. The official guide discourages that layer.
- Each page has a `ui/` folder and a `model/` folder. Add `api/`, `lib/` or `config/` only when a file goes into it.
- A page view is a child component. It gets data as props and actions as `action` props.
- Page state and actions stay members of the root component, in `members` files in the page `model/` folder.
- Resources and mutations that two or more pages use stay in `app.contract`. Exact has no cache that component instances share.
- Exact has no re-export. The public file of a slice is the file with the slice name. Do not import other files of a slice from outside.
- End-to-end tests stay at the root as `<page>.test.contract`. Exact finds tests only beside `app.json`.
- Name a file for its content (`draft.contract`), not for its technical role (`utils.contract`).

Rejected: the six layers from the start. This app has three screens and thin views. Most layers would hold one file.

## Decision 3: tools

- Exact transpiles and bundles (`rolldown`). The app does not choose that tool.
- `oxlint` lints TypeScript with its default rules. Type-aware rules stay off. `contract build` does the type check.
- `oxfmt` formats TypeScript. Pin an exact version. `contract fmt` formats `.contract` files.
- Do not use Steiger. It reads TypeScript imports and `index.ts`, not `use` lines. `rules.test.ts` checks the import direction.

## Order of work

1. Gates: one format commit, git hooks, the pinned Exact commit, CI lint.
2. Mechanical split into `pages/` and `shared/`. No behaviour change. The seam does not change.
3. `HabitDb` interface and fake. The seam does not change.

## Consequences

- A new view ticket edits one page folder and one test file.
- The data module has more files than before.
- If the fake and SQLite differ, the shared test suite shows it only when SQLite runs in `bun test`.
