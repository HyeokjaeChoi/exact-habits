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
