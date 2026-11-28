// Pure streak math on YYYY-MM-DD day keys. No clock, no Exact imports.

export function addDays(day: string, n: number): string {
  const [y, m, d] = day.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d + n)).toISOString().slice(0, 10);
}

/** The Sunday on or before day. */
export function weekStart(day: string): string {
  const [y, m, d] = day.split("-").map(Number);
  return addDays(day, -new Date(Date.UTC(y, m - 1, d)).getUTCDay());
}

/** The 28 days of four whole weeks, oldest first: from the Sunday three weeks before this week's, to this week's Saturday. */
export function calendarDays(today: string): string[] {
  const first = addDays(weekStart(today), -21);
  return Array.from({ length: 28 }, (_, i) => addDays(first, i));
}

export function stats(
  doneDays: string[],
  today: string,
): { doneToday: boolean; streak: number; best: number; total: number } {
  const days = new Set(doneDays.filter((d) => d <= today)); // YYYY-MM-DD sorts as text; later days (clock moved back) ignored
  const doneToday = days.has(today);
  let streak = 0;
  for (let d = doneToday ? today : addDays(today, -1); days.has(d); d = addDays(d, -1)) streak++;
  let best = 0;
  for (const d of days) {
    if (days.has(addDays(d, -1))) continue; // not the start of a run
    let len = 0;
    for (let e = d; days.has(e); e = addDays(e, 1)) len++;
    best = Math.max(best, len);
  }
  return { doneToday, streak, best, total: days.size };
}
