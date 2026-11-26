import { expect, test } from 'bun:test';
import { addDays, lastDays, stats } from './streak.ts';

test('addDays crosses month, year and leap day', () => {
  expect(addDays('2026-03-31', 1)).toBe('2026-04-01');
  expect(addDays('2026-01-01', -1)).toBe('2025-12-31');
  expect(addDays('2028-02-28', 1)).toBe('2028-02-29');
  expect(addDays('2028-02-29', 1)).toBe('2028-03-01');
  expect(addDays('2026-02-28', 1)).toBe('2026-03-01');
});

test('lastDays is oldest first and ends today', () => {
  expect(lastDays('2026-03-02', 3)).toEqual(['2026-02-28', '2026-03-01', '2026-03-02']);
  expect(lastDays('2026-03-02', 28)).toHaveLength(28);
});

const T = '2026-03-14';
test('empty', () => expect(stats([], T)).toEqual({ doneToday: false, streak: 0, best: 0, total: 0 }));
test('only today', () => expect(stats([T], T)).toEqual({ doneToday: true, streak: 1, best: 1, total: 1 }));
test('only yesterday keeps the streak alive', () =>
  expect(stats(['2026-03-13'], T)).toEqual({ doneToday: false, streak: 1, best: 1, total: 1 }));
test('a missed day resets the streak, best is kept', () =>
  expect(stats(['2026-03-10', '2026-03-11', '2026-03-12'], T)).toEqual({ doneToday: false, streak: 0, best: 3, total: 3 }));
test('best greater than current streak', () =>
  expect(stats(['2026-03-01', '2026-03-02', '2026-03-03', '2026-03-04', '2026-03-13', T], T))
    .toEqual({ doneToday: true, streak: 2, best: 4, total: 6 }));
test('runs cross a month and year boundary', () =>
  expect(stats(['2025-12-30', '2025-12-31', '2026-01-01'], '2026-01-02')).toEqual({ doneToday: false, streak: 3, best: 3, total: 3 }));
test('runs cross a leap day', () =>
  expect(stats(['2028-02-28', '2028-02-29', '2028-03-01'], '2028-03-01')).toEqual({ doneToday: true, streak: 3, best: 3, total: 3 }));
test('future days are ignored', () =>
  expect(stats(['2026-03-15', '2026-03-16', T], T)).toEqual({ doneToday: true, streak: 1, best: 1, total: 1 }));
test('duplicates and unordered input count once', () =>
  expect(stats([T, '2026-03-13', T, '2026-03-13'], T)).toEqual({ doneToday: true, streak: 2, best: 2, total: 2 }));
