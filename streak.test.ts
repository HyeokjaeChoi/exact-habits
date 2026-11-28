import { expect, test } from "bun:test";
import { addDays, calendarDays, stats, weekStart } from "./streak.ts";

test("addDays crosses month, year and leap day", () => {
  expect(addDays("2026-03-31", 1)).toBe("2026-04-01");
  expect(addDays("2026-01-01", -1)).toBe("2025-12-31");
  expect(addDays("2028-02-28", 1)).toBe("2028-02-29");
  expect(addDays("2028-02-29", 1)).toBe("2028-03-01");
  expect(addDays("2026-02-28", 1)).toBe("2026-03-01");
});

const dow = (day: string) => new Date(day + "T00:00:00Z").getUTCDay();

test("weekStart is the Sunday on or before the day", () => {
  expect(weekStart("2026-03-08")).toBe("2026-03-08"); // a Sunday
  expect(weekStart("2026-03-14")).toBe("2026-03-08"); // a Saturday
  expect(weekStart("2026-03-11")).toBe("2026-03-08"); // a Wednesday
});

test("weekStart crosses month and year boundaries", () => {
  expect(weekStart("2026-04-01")).toBe("2026-03-29");
  expect(weekStart("2026-01-01")).toBe("2025-12-28");
});

test("weekStart is right across the US DST change on 2026-03-08", () => {
  expect(weekStart("2026-03-07")).toBe("2026-03-01");
  expect(weekStart("2026-03-09")).toBe("2026-03-08");
  expect(weekStart("2026-03-10")).toBe("2026-03-08");
});

test("calendarDays is 28 aligned days, Sunday to Saturday, holding today", () => {
  for (const today of ["2026-03-14", "2026-03-08", "2026-03-11", "2026-01-01", "2028-03-01"]) {
    const days = calendarDays(today);
    expect(days).toHaveLength(28);
    expect(dow(days[0])).toBe(0);
    expect(dow(days[27])).toBe(6);
    expect(days).toContain(today);
  }
  const days = calendarDays("2026-03-14"); // Saturday: today is the last cell
  expect(days[0]).toBe("2026-02-15");
  expect(days[27]).toBe("2026-03-14");
  expect(calendarDays("2026-03-11")[27]).toBe("2026-03-14"); // Wednesday: three cells to come
});

const T = "2026-03-14";
test("empty", () =>
  expect(stats([], T)).toEqual({ doneToday: false, streak: 0, best: 0, total: 0 }));
test("only today", () =>
  expect(stats([T], T)).toEqual({ doneToday: true, streak: 1, best: 1, total: 1 }));
test("only yesterday keeps the streak alive", () =>
  expect(stats(["2026-03-13"], T)).toEqual({ doneToday: false, streak: 1, best: 1, total: 1 }));
test("a missed day resets the streak, best is kept", () =>
  expect(stats(["2026-03-10", "2026-03-11", "2026-03-12"], T)).toEqual({
    doneToday: false,
    streak: 0,
    best: 3,
    total: 3,
  }));
test("best greater than current streak", () =>
  expect(
    stats(["2026-03-01", "2026-03-02", "2026-03-03", "2026-03-04", "2026-03-13", T], T),
  ).toEqual({ doneToday: true, streak: 2, best: 4, total: 6 }));
test("runs cross a month and year boundary", () =>
  expect(stats(["2025-12-30", "2025-12-31", "2026-01-01"], "2026-01-02")).toEqual({
    doneToday: false,
    streak: 3,
    best: 3,
    total: 3,
  }));
test("runs cross a leap day", () =>
  expect(stats(["2028-02-28", "2028-02-29", "2028-03-01"], "2028-03-01")).toEqual({
    doneToday: true,
    streak: 3,
    best: 3,
    total: 3,
  }));
test("future days are ignored", () =>
  expect(stats(["2026-03-15", "2026-03-16", T], T)).toEqual({
    doneToday: true,
    streak: 1,
    best: 1,
    total: 1,
  }));
test("duplicates and unordered input count once", () =>
  expect(stats([T, "2026-03-13", T, "2026-03-13"], T)).toEqual({
    doneToday: true,
    streak: 2,
    best: 2,
    total: 2,
  }));
