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

export function rsi(values: number[], period: number): Array<number | null> {
  if (values.length <= period) return values.map(() => null);
  const result: Array<number | null> = values.map(() => null);
  let gainSum = 0;
  let lossSum = 0;

  for (let index = 1; index <= period; index += 1) {
    const diff = values[index] - values[index - 1];
    if (diff >= 0) gainSum += diff;
    else lossSum += Math.abs(diff);
  }

  let avgGain = gainSum / period;
  let avgLoss = lossSum / period;
  result[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);

  for (let index = period + 1; index < values.length; index += 1) {
    const diff = values[index] - values[index - 1];
    const gain = diff > 0 ? diff : 0;
    const loss = diff < 0 ? Math.abs(diff) : 0;
    avgGain = (avgGain * (period - 1) + gain) / period;
    avgLoss = (avgLoss * (period - 1) + loss) / period;
    result[index] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }

  return result;
}

export function rsiLine(candles: CandlePoint[], period: number): LinePoint[] {
  const closes = candles.map((item) => Number(item.close));
  const values = rsi(closes, period);
  const points: LinePoint[] = [];
  values.forEach((value, index) => {
    if (value === null) return;
    points.push({ time: toUnixTime(candles[index].timestamp), value });
  });
  return points;
}

export function trueRanges(candles: CandlePoint[]): number[] {
  return candles.map((item, index) => {
    const high = Number(item.high);
    const low = Number(item.low);
    if (index === 0) return high - low;
    const previousClose = Number(candles[index - 1].close);
    return Math.max(high - low, Math.abs(high - previousClose), Math.abs(low - previousClose));
  });
}

export function atr(candles: CandlePoint[], period: number): Array<number | null> {
  const ranges = trueRanges(candles);
  if (ranges.length < period) return ranges.map(() => null);
  const result: Array<number | null> = ranges.map(() => null);
  let previousAtr = ranges.slice(0, period).reduce((sum, item) => sum + item, 0) / period;
  result[period - 1] = previousAtr;

  for (let index = period; index < ranges.length; index += 1) {
    previousAtr = (previousAtr * (period - 1) + ranges[index]) / period;
    result[index] = previousAtr;
  }
  return result;
}

export function atrLine(candles: CandlePoint[], period: number): LinePoint[] {
  const values = atr(candles, period);
  const points: LinePoint[] = [];
  values.forEach((value, index) => {
    if (value === null) return;
    points.push({ time: toUnixTime(candles[index].timestamp), value });
  });
  return points;
}

export function lastValue(points: LinePoint[]): number | null {
  if (!points.length) return null;
  return points[points.length - 1].value;
}
