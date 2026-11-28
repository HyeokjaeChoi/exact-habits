import { Database } from "bun:sqlite";
import { expect, test } from "bun:test";
import { answer } from "./app.ts";

// A one-file stand-in for the sqlite grant: bun:sqlite behind the same open/execute/query/close.
function storage(db: Database): any {
  return {
    sqlite: {
      open: async () => ({
        execute: async (sql: string, args: unknown[] = []) => ({
          changes: db.query(sql).run(...(args as any[])).changes,
        }),
        query: async (sql: string, args: unknown[] = []) => ({
          rows: db.query(sql).values(...(args as any[])),
        }),
        close: async () => {},
      }),
    },
  };
}
const load = (s: any) =>
  answer("loadHabits", ["2026-03-14"], undefined as any, s, undefined as any) as Promise<any[]>;
const add = (s: any, ...a: string[]) =>
  answer("addHabit", a as any, undefined as any, s, undefined as any) as Promise<any>;

test("a database from before icon and colour keeps its habits and check-ins, with the defaults", async () => {
  const db = new Database(":memory:");
  db.run(
    "CREATE TABLE habits (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, name_key TEXT NOT NULL UNIQUE)",
  );
  db.run(
    "CREATE TABLE checkins (habit_id INTEGER NOT NULL, day TEXT NOT NULL, PRIMARY KEY (habit_id, day))",
  );
  db.run("INSERT INTO habits (name, name_key) VALUES ('Read', 'read')");
  db.run("INSERT INTO checkins VALUES (1, '2026-03-14')");
  const s = storage(db);
  for (let i = 0; i < 2; i++) {
    // opening twice must not fail
    const [h] = await load(s);
    expect(h).toMatchObject({
      id: "1",
      name: "Read",
      icon: "sparkles",
      color: "orange",
      doneToday: true,
      total: 1,
    });
  }
  expect(await add(s, "Run", "running", "blue")).toEqual({ ok: true, error: "" });
  expect((await load(s))[1]).toMatchObject({ name: "Run", icon: "running", color: "blue" });
});

test("an unknown icon or colour falls back to the default, on write and on read", async () => {
  const db = new Database(":memory:");
  const s = storage(db);
  await add(s, "A", "nope", "plaid");
  db.run(
    "INSERT INTO habits (name, name_key, icon, color) VALUES ('B', 'b', 'future', 'chartreuse')",
  );
  expect((await load(s)).map((h) => [h.icon, h.color])).toEqual([
    ["sparkles", "orange"],
    ["sparkles", "orange"],
  ]);
});
