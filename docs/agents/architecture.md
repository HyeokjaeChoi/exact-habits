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
| entry file (one per app) | `app.ts` | `answer` dispatches each source name to its function. `grants` declares the storage and network that the data module may use. Exact loads only this file. |
| domain | `domain/` | Pure logic: streak math, calendar days. |
| data | `data/` | SQLite: schema, migration, queries. |

`app.ts` is not a layer of its own. It is one entry file. Features split their code into `domain/` and `data/` files, and `app.ts` imports them.

How one request flows:

1. A view declares `resource habits = loadHabits(today)`, or an action runs `send checked = setDone(…)`.
2. The Exact runtime calls `answer("setDone", args, …)` in `app.ts`.
3. `answer` calls `sources.setDone`. That function writes SQLite and returns a `Reply`.
4. The mutation line `checked … refreshes habits, days` makes the runtime call `loadHabits` and `loadDays` again.
5. The view renders again from the new resource values.

Android comparison:

| Exact | Android |
|---|---|
| `app.contract` routes and root component | Activity and `NavHost` (Navigation Compose) |
| `resource` / `mutation` lines | ViewModel state that calls a repository |
| `answer` in `app.ts` | The call from a ViewModel to a repository, wired by Exact |
| `grants` in `app.ts` | `<uses-permission>` in the manifest, for the data module only |

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
