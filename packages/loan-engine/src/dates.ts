/**
 * Calendar dates as ISO strings ("YYYY-MM-DD"). No times or time zones are
 * involved anywhere in the engine, so a date always means the same day.
 */
export type IsoDate = string;

const ISO = /^(\d{4})-(\d{2})-(\d{2})$/;

export interface CalendarDate {
  year: number;
  month: number; // 1-12
  day: number; // 1-31
}

export function daysInMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

export function parseIsoDate(value: IsoDate): CalendarDate {
  const m = ISO.exec(value);
  if (!m) throw new RangeError(`Not a date in YYYY-MM-DD form: ${value}`);
  const [year, month, day] = [Number(m[1]), Number(m[2]), Number(m[3])];
  if (month < 1 || month > 12 || day < 1 || day > daysInMonth(year, month)) {
    throw new RangeError(`Not a real calendar date: ${value}`);
  }
  return { year, month, day };
}

export function isValidIsoDate(value: unknown): value is IsoDate {
  if (typeof value !== "string") return false;
  try {
    parseIsoDate(value);
    return true;
  } catch {
    return false;
  }
}

export function formatIsoDate(d: CalendarDate): IsoDate {
  const pad = (n: number, w: number) => String(n).padStart(w, "0");
  return `${pad(d.year, 4)}-${pad(d.month, 2)}-${pad(d.day, 2)}`;
}

/**
 * The same day of the month, `months` later (or earlier, if negative).
 * A day that does not exist in the target month becomes that month's last
 * day; the original day returns when it exists again (B-05).
 */
export function addMonths(start: IsoDate, months: number): IsoDate {
  const s = parseIsoDate(start);
  const total = s.year * 12 + (s.month - 1) + months;
  const year = Math.floor(total / 12);
  const month = total - year * 12 + 1;
  return formatIsoDate({ year, month, day: Math.min(s.day, daysInMonth(year, month)) });
}

/** ISO dates compare correctly as strings. */
export function compareDates(a: IsoDate, b: IsoDate): number {
  return a < b ? -1 : a > b ? 1 : 0;
}
