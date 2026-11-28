# Architecture (target state, not yet applied)

Status: TARGET. The code is still flat: `app.contract`, `app.ts`, `streak.ts`.
Do not move a file unless the ticket is the restructure ticket.
The decisions and their reasons are in `docs/adr/0001-habitdb-interface-and-fsd-pages-first.md`.

## Views: Feature-Sliced Design v2.1, pages first

Read the `feature-sliced-design` skill before you decide where view code goes.

```text
app.contract              routes, root component, shared resources and mutations
pages/<today|habit|add>/
  ui/                     the page view: a child component
  model/                  the page state and actions: `members` files of the root
shared/                   seam shapes, `fn`s and UI parts with no business meaning
<page>.test.contract      end-to-end tests, at the root
```

| Layer, high to low | Place | Holds |
|---|---|---|
| app | `app.contract` | Routes, root component, resources and mutations that two or more pages use |
| pages | `pages/<page>/` | One screen for each route, with its own state and actions |
| features | `features/<feature>/` | Add only when the extraction rule holds |
| entities | `entities/<entity>/` | Add only when the extraction rule holds |
| shared | `shared/` | Seam shapes (`Habit`, `DayMark`), `fn`s and UI parts with no business meaning |

The extraction rule: move code out of a page only when all three are true.

1. Two or more places use the same code now.
2. The code has a reason to change that does not depend on one user of it.
3. The boundary has one responsibility.

Rules:

1. A file imports only from a layer below its own layer.
2. A slice does not import another slice on the same layer.
3. `shared/` imports from no other layer.
4. Do not add `widgets/`.
5. A page has `ui/` and `model/`. Add `api/`, `lib/` or `config/` only when a file goes into it.
6. The public file of a slice has the slice name. Do not import other files of a slice from outside.
7. Name a file for its content, not for its technical role.
8. The seam in `SPEC.md` does not change in the restructure.

How this differs from React:

- A page view is a child component. It gets data as props and actions as `action` props.
- `members "./pages/add/model/draft.contract"` splits root state and actions into files. Each file sees each member.
- Exact has no cache that component instances share. A child mutation refreshes only its own resources. Thus shared resources stay in `app.contract`.
- Exact has no re-export, so a slice has no `index` file.
- Exact finds tests only beside `app.json`. Tests cannot sit in a page folder.

## TypeScript: the data module

The data module is not part of Feature-Sliced Design. It is the local backend behind the seam.

| Place | Holds |
|---|---|
| `app.ts` (one entry file) | `answer` dispatches each source name to its function. `grants` declares the storage and network that the data module may use. Exact loads only this file. |
| `model/` | Pure rules (streak math, calendar days) and the `HabitDb` interface. |
| `db/` | The SQLite implementation of `HabitDb`, the schema and the migration. |

Rules:

1. The import direction is `app.ts`, then `db/`, then `model/`.
2. `model/` is pure. It does not open SQLite, read the clock, or import `db/` or `app.ts`.
3. Only `db/` contains SQL.
4. A `model/` function takes a `HabitDb` as its first argument. `app.ts` passes the SQLite one.
5. `fakeHabitDb()` is the in-memory `HabitDb` for unit tests.
6. A unit test sits next to its file: `model/streak.test.ts`.
7. Do not add an `index.ts` that re-exports.

How one request flows:

1. A view declares `resource habits = loadHabits(today)`, or an action runs `send checked = setDone(…)`.
2. The Exact runtime calls `answer("setDone", args, …)` in `app.ts`.
3. `answer` calls the `model/` function with the SQLite `HabitDb`. The function returns a `Reply`.
4. The mutation line `checked … refreshes habits, days` makes the runtime call `loadHabits` and `loadDays` again.
5. The view renders again from the new resource values.

Android comparison:

| Exact | Android |
|---|---|
| `app.contract` routes and root component | Activity and `NavHost` (Navigation Compose) |
| `pages/<page>/` | A `:feature:<page>` module and its screen |
| `resource` / `mutation` lines | ViewModel state that calls a repository |
| `answer` in `app.ts` | The call from a ViewModel to a repository, wired by Exact |
| `HabitDb` in `model/`, SQLite in `db/` | A repository interface and its Room implementation, wired by hand |
| `grants` in `app.ts` | `<uses-permission>` in the manifest, for the data module only |

## Mechanical checks to add with the restructure

Add these to `rules.test.ts`:

1. Read each `use … from "./…contract"` and `members "./…contract"` line. Fail if the import goes up, or across slices on one layer.
2. Read each `import` in `model/**`. Fail if the path leaves `model/`.
3. Fail if a file outside `db/` contains SQL keywords in a string.
4. Fail if the generated `Sources` types differ from the snapshot (the seam).

After the restructure PR merges, move the rules into `.claude/rules/` with `paths:` for each folder.
