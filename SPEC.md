# Habits: spec and seam

A daily habit tracker for web, iOS and macOS, built on Exact. Each file has one owner:

| File | Owner | Holds |
|---|---|---|
| `app.contract` | UI | The view. Seam declarations are fixed (below). |
| `app.ts`, `streak.ts`, `streak.test.ts` | Data | The SQLite data module and the pure streak math, with its unit test. |
| `app.test.contract` | Tests | End-to-end tests by `testId`. |

## Seam (do not change)

The following in `app.contract` keep their names, arguments and types: the `routes`, the
`shape`s, the `fn`s, the `resource`/`mutation` lines, and the actions `step`, `back`, `follow`,
`openAdd`, `editName`, `save`, `afterSave`, `toggle`, `askRemove` and `remove`. The UI may add
state, derives, actions, `fn`s and components of its own.

Sources, as `app.contract.d.ts` declares them:

| Source | Args | Result | Behaviour |
|---|---|---|---|
| `loadHabits` | `[today]` | `Habit[]` | Every habit, oldest first (by id ascending), with `doneToday`, `streak`, `best`, `total` computed for `today`. |
| `loadDays` | `[id, today]` | `DayMark[]` | 28 entries, oldest first, the last one `today`: `{day, done}`. Unknown id: 28 entries, all not done. |
| `addHabit` | `[name]` | `Reply` | Name is already trimmed. Unique case-insensitively (JS `toLowerCase`, stored as a key column with a UNIQUE constraint). Duplicate: `{ok: false, error: "A habit called <existing name> already exists."}`. |
| `setDone` | `[id, day, done]` | `Reply` | Idempotent: `true` inserts the (id, day) check-in if absent, `false` deletes it. |
| `removeHabit` | `[id]` | `Reply` | Deletes the habit and its check-ins. |

Day keys are `YYYY-MM-DD` in the person's own zone; the data module never reads the clock
(Exact refuses `Date.now`); "today" always arrives as an argument. Day arithmetic is calendar
arithmetic on the key (`new Date(Date.UTC(y, m - 1, d + n))`), never `ms ± 86400000` on local time.

Streak rules:
- `total`: the number of days checked.
- `streak`: the run of consecutive checked days ending today if today is checked, else ending
  yesterday if yesterday is checked (a streak stays alive until a whole day is missed), else 0.
- `best`: the longest run ever; always `>= streak`.
- Check-ins after `today` (a clock moved back) are ignored by all three.

## Screens and testIds

Text formats come from the seam's `fn`s: `streakText(n)` is `No streak`, `1-day streak`,
`5-day streak`; `dayCount(n)` is `1 day`, `5 days`.

**Today** (route `today`, `/`)
- `app`: the `main`.
- `add-habit`: the header's add button (symbol, `aria-label="Add Habit"`).
- `today-date`: the date under the title, `formatDate(shown, time.utcOffset, "medium")`, e.g. `Mar 14, 2026`.
- `progress`: text `<done> of <total> done`, e.g. `1 of 3 done`; shown only when there is at least one habit. Under it, a native determinate `progress` bar (testId `progress-bar`, accessible name "Today’s progress") filled `done / total`; shown and hidden with the text.
- `empty-add`: the `EmptyState`'s button when there are no habits (title `No Habits`).
- Per habit `h`, a row holding:
  - `check-<id>`: a checkbox for today, `checked=h.doneToday change=toggle(h.id)`, `aria-label` the habit's name.
  - `name-<id>`: the name.
  - `streak-<id>`: `streakText(h.streak)`.
  - `open-<id>`: a link to `path("habit", h.id)` (chevron symbol), `aria-label` `Details for <name>`.
  - The row swipes to delete (`delete=remove(h.id)`) without asking.

**Habit** (route `habit`, `/habit/:id`)
- `detail-title`: the heading, the habit's name, or `Not Found` once loaded and the id names nothing.
- `detail-streak`: wraps the first section's `SummaryCard` (`exact:content`, in a transparent section, centred, at most `26.25rem` wide): label `Current Streak`, value `h.streak` as a number, detail `day in a row` when the streak is 1 and `days in a row` otherwise, progress `min(1, streak / best)` when `best > 0` (absent when `best == 0`). A text read of `detail-streak` joins the three texts without separators, e.g. `Current Streak2days in a row`. There is no `Streak` row.
- `detail-best`, `detail-total`: `dayCount` of each, rows in the section under the `Done Today` switch.
- `detail-check`: a switch for today, same `toggle(h.id)`.
- `history`: the last 28 days (`days`), seven to a row, oldest first; each day `day-<YYYY-MM-DD>` showing done or not (`DoneMark` from `exact:content`).
- `delete-habit`: a destructive button, `askRemove(h.id)`; the alert `remove` then offers `remove-confirm` and `remove-cancel`. Confirming goes back to Today.
- `missing-back`: on `Not Found`, a button back to Today.

**Add** (route `add`, `/add`, a modal sheet)
- `add-name`: the name field, `submit=save`, autofocus.
- `add-save`: disabled while the trimmed name is empty or the save is pending.
- `add-cancel`: closes the sheet.
- `add-error`: the last refusal (`refusal`), red, under the field; absent when empty.
- `add-hint`: `saveHint` in the section's footer.

## Non-goals (v1)

No reminders or notifications, no editing a habit's name, no per-week targets, no sync.
