export type CandlePoint = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

export type LinePoint = {
  time: number;
  value: number;
};

export function toUnixTime(timestamp: string) {
  return Math.floor(new Date(timestamp).getTime() / 1000);
}

export function ema(values: number[], period: number): Array<number | null> {
  if (period <= 1) return values.map((value) => value);
  const result: Array<number | null> = [];
  const multiplier = 2 / (period + 1);
  let previous: number | null = null;

  for (let index = 0; index < values.length; index += 1) {
    const value = Number(values[index]);
    if (index < period - 1) {
      result.push(null);
      continue;
    }
    if (previous === null) {
      const seed = values.slice(index - period + 1, index + 1).reduce((sum, item) => sum + Number(item), 0) / period;
      previous = seed;
      result.push(seed);
      continue;
    }
    const next = value * multiplier + previous * (1 - multiplier);
    previous = next;
    result.push(next);
  }

  return result;
}

export function emaLine(candles: CandlePoint[], period: number): LinePoint[] {
  const closes = candles.map((item) => Number(item.close));
  const values = ema(closes, period);
  const points: LinePoint[] = [];
  values.forEach((value, index) => {
    if (value === null) return;
    points.push({ time: toUnixTime(candles[index].timestamp), value });
  });
  return points;
}
