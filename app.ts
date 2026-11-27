import type { Answer, Database, Result, Sources, Storage } from './app.contract.d.ts';
import { calendarDays, stats } from './streak.ts';

const DB = 'app:/data/habits.db';
const ICONS = ['sparkles', 'book', 'running', 'walking', 'heart', 'moon', 'star', 'timer'];
const COLORS = ['orange', 'red', 'green', 'blue', 'purple', 'teal'];
// Unknown values (an older or newer database, a stray caller) fall back to the default.
const pick = (list: string[], v: unknown) => (list.includes(String(v)) ? String(v) : list[0]);
export const grants = `sqlite.open ${DB}`;
let last: Promise<unknown> = Promise.resolve();

// Serialized; close after each answer: on the web an open database holds its cross-tab lock.
function use<T>(storage: Storage, work: (db: Database) => Promise<T>): Promise<T> {
  const run = last.then(async () => {
    const db = await storage.sqlite.open(DB);
    try {
      await db.execute('CREATE TABLE IF NOT EXISTS habits (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE, icon TEXT NOT NULL DEFAULT \'sparkles\', color TEXT NOT NULL DEFAULT \'orange\')');
      await db.execute('CREATE TABLE IF NOT EXISTS checkins (habit_id INTEGER NOT NULL, day TEXT NOT NULL, PRIMARY KEY (habit_id, day))');
      // Additive migration for a database made before icon and colour existed.
      const have = new Set((await db.query('PRAGMA table_info(habits)')).rows.map(r => String(r[1])));
      if (!have.has('icon')) await db.execute("ALTER TABLE habits ADD COLUMN icon TEXT NOT NULL DEFAULT 'sparkles'");
      if (!have.has('color')) await db.execute("ALTER TABLE habits ADD COLUMN color TEXT NOT NULL DEFAULT 'orange'");
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
    return (await db.query('SELECT id, name, icon, color FROM habits ORDER BY id ASC')).rows.map(([id, name, icon, color]) => {
      const { doneToday, streak, best, total } = stats(days.get(String(id)) ?? [], today);
      return { id: String(id), name: String(name), icon: pick(ICONS, icon), color: pick(COLORS, color), doneToday, streak, best, total };
    });
  }),
  loadDays: ([id, today], _store, storage) => use(storage, async (db): Promise<Result<'loadDays'>> => {
    const done = new Set((await db.query('SELECT day FROM checkins WHERE habit_id = ?', [id])).rows.map(([day]) => String(day)));
    return calendarDays(today).map(day => ({ day, done: day <= today && done.has(day), future: day > today }));
  }),
  addHabit: ([name, icon, color], _store, storage) => use(storage, async db => {
    const key = name.toLowerCase(); // JavaScript's Unicode lowercasing, not SQLite's ASCII-only lower().
    const result = await db.execute('INSERT INTO habits (name, name_key, icon, color) VALUES (?, ?, ?, ?) ON CONFLICT(name_key) DO NOTHING', [name, key, pick(ICONS, icon), pick(COLORS, color)]);
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
