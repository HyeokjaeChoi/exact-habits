import type { Answer, Database, Result, Sources, Storage } from './app.contract.d.ts';
import { lastDays, stats } from './streak.ts';

const DB = 'app:/data/habits.db';
export const grants = `sqlite.open ${DB}`;
let last: Promise<unknown> = Promise.resolve();

// Serialized; close after each answer: on the web an open database holds its cross-tab lock.
function use<T>(storage: Storage, work: (db: Database) => Promise<T>): Promise<T> {
  const run = last.then(async () => {
    const db = await storage.sqlite.open(DB);
    try {
      await db.execute('CREATE TABLE IF NOT EXISTS habits (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE)');
      await db.execute('CREATE TABLE IF NOT EXISTS checkins (habit_id INTEGER NOT NULL, day TEXT NOT NULL, PRIMARY KEY (habit_id, day))');
      return await work(db);
    } finally { await db.close(); }
  });
  last = run.catch(() => {});
  return run;
}
const saved = (): Result<'addHabit'> => ({ ok: true, error: '' });
const sources: Sources = {
  loadHabits: ([today], _store, storage) => use(storage, async (db): Promise<Result<'loadHabits'>> => {
    const days = new Map<string, string[]>();
    for (const [id, day] of (await db.query('SELECT habit_id, day FROM checkins')).rows) {
      const k = String(id);
      days.set(k, [...(days.get(k) ?? []), String(day)]);
    }
    return (await db.query('SELECT id, name FROM habits ORDER BY id ASC')).rows.map(([id, name]) => {
      const { doneToday, streak, best, total } = stats(days.get(String(id)) ?? [], today);
      return { id: String(id), name: String(name), doneToday, streak, best, total };
    });
  }),
  loadDays: ([id, today], _store, storage) => use(storage, async (db): Promise<Result<'loadDays'>> => {
    const done = new Set((await db.query('SELECT day FROM checkins WHERE habit_id = ?', [id])).rows.map(([day]) => String(day)));
    return lastDays(today, 28).map(day => ({ day, done: done.has(day) }));
  }),
  addHabit: ([name], _store, storage) => use(storage, async db => {
    const key = name.toLowerCase(); // JavaScript's Unicode lowercasing, not SQLite's ASCII-only lower().
    const result = await db.execute('INSERT INTO habits (name, name_key) VALUES (?, ?) ON CONFLICT(name_key) DO NOTHING', [name, key]);
    if (result.changes) return saved();
    const { rows } = await db.query('SELECT name FROM habits WHERE name_key = ?', [key]);
    return { ok: false, error: `A habit called ${String(rows[0]?.[0] ?? name)} already exists.` };
  }),
  setDone: ([id, day, done], _store, storage) => use(storage, async db => {
    if (done) await db.execute('INSERT OR IGNORE INTO checkins (habit_id, day) VALUES (?, ?)', [id, day]);
    else await db.execute('DELETE FROM checkins WHERE habit_id = ? AND day = ?', [id, day]);
    return saved();
  }),
  removeHabit: ([id], _store, storage) => use(storage, async db => {
    await db.execute('DELETE FROM checkins WHERE habit_id = ?', [id]);
    await db.execute('DELETE FROM habits WHERE id = ?', [id]);
    return saved();
  }),
};
export const answer: Answer = (source, args, store, storage, native) => sources[source](args, store, storage, native);
