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

export type BollingerBands = {
  middle: LinePoint[];
  upper: LinePoint[];
  lower: LinePoint[];
};

export type MacdPoint = {
  time: number;
  macd: number;
  signal: number;
  histogram: number;
};

export function toUnixTime(timestamp: string) {
  return Math.floor(new Date(timestamp).getTime() / 1000);
}

export function sma(values: number[], period: number): Array<number | null> {
  const result: Array<number | null> = values.map(() => null);
  if (period <= 0) return result;
  let sum = 0;
  for (let index = 0; index < values.length; index += 1) {
    sum += Number(values[index]);
    if (index >= period) sum -= Number(values[index - period]);
    if (index >= period - 1) result[index] = sum / period;
  }
  return result;
}

export function stddevWindow(values: number[], endIndex: number, period: number): number | null {
  if (endIndex < period - 1) return null;
  const slice = values.slice(endIndex - period + 1, endIndex + 1);
  const mean = slice.reduce((sum, item) => sum + Number(item), 0) / period;
  const variance = slice.reduce((sum, item) => sum + Math.pow(Number(item) - mean, 2), 0) / period;
  return Math.sqrt(variance);
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

export function bollingerBands(candles: CandlePoint[], period = 20, multiplier = 2): BollingerBands {
  const closes = candles.map((item) => Number(item.close));
  const middleValues = sma(closes, period);
  const middle: LinePoint[] = [];
  const upper: LinePoint[] = [];
  const lower: LinePoint[] = [];

  middleValues.forEach((middleValue, index) => {
    if (middleValue === null) return;
    const stdev = stddevWindow(closes, index, period);
    if (stdev === null) return;
    const time = toUnixTime(candles[index].timestamp);
    middle.push({ time, value: middleValue });
    upper.push({ time, value: middleValue + stdev * multiplier });
    lower.push({ time, value: middleValue - stdev * multiplier });
  });

  return { middle, upper, lower };
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

export function macdPoints(candles: CandlePoint[], fast = 12, slow = 26, signalPeriod = 9): MacdPoint[] {
  const closes = candles.map((item) => Number(item.close));
  const fastEma = ema(closes, fast);
  const slowEma = ema(closes, slow);
  const macdValues: Array<number | null> = closes.map((_, index) => {
    if (fastEma[index] === null || slowEma[index] === null) return null;
    return Number(fastEma[index]) - Number(slowEma[index]);
  });

  const compactMacd = macdValues.filter((value): value is number => value !== null);
  const compactSignal = ema(compactMacd, signalPeriod);
  const firstMacdIndex = macdValues.findIndex((value) => value !== null);
  const points: MacdPoint[] = [];

  compactSignal.forEach((signalValue, compactIndex) => {
    if (signalValue === null) return;
    const candleIndex = firstMacdIndex + compactIndex;
    const macdValue = macdValues[candleIndex];
    if (macdValue === null || candleIndex < 0 || !candles[candleIndex]) return;
    points.push({
      time: toUnixTime(candles[candleIndex].timestamp),
      macd: macdValue,
      signal: signalValue,
      histogram: macdValue - signalValue,
    });
  });

  return points;
}

export function lastValue(points: LinePoint[]): number | null {
  if (!points.length) return null;
  return points[points.length - 1].value;
}
