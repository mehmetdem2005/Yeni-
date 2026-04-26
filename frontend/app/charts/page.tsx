import { ChartControls } from '@/components/ChartControls';
import { IndicatorPanelChart } from '@/components/IndicatorPanelChart';
import { LightweightCandles } from '@/components/LightweightCandles';
import { MobileNav } from '@/components/MobileNav';
import { apiGet } from '@/lib/api';
import { atrLine, rsiLine, lastValue } from '@/lib/chart-indicators';

type Candle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type ChartResponse = {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  live_filled?: boolean;
};

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined, fallback: string) {
  if (Array.isArray(value)) return value[0] ?? fallback;
  return value ?? fallback;
}

function boolParam(value: string | string[] | undefined, fallback: boolean) {
  const raw = first(value, String(fallback));
  return raw !== 'false';
}

function fmt(value: number | null) {
  if (value === null) return '—';
  return value.toFixed(2);
}

async function getChart(symbol: string, timeframe: string): Promise<ChartResponse> {
  try {
    return await apiGet<ChartResponse>(`/api/chart/${symbol}/${timeframe}?limit=300`);
  } catch {
    return { symbol: symbol.replace('USDT', '/USDT'), timeframe, candles: [] };
  }
}

export default async function ChartsPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const symbol = first(params.symbol, 'BTCUSDT');
  const timeframe = first(params.timeframe, '1h');
  const showVolume = boolParam(params.volume, true);
  const showEma = boolParam(params.ema, true);
  const showRsi = boolParam(params.rsi, true);
  const showAtr = boolParam(params.atr, true);
  const chart = await getChart(symbol, timeframe);
  const rsiPoints = rsiLine(chart.candles, 14);
  const atrPoints = atrLine(chart.candles, 14);

  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 12 }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>GRAFİKLER</div>
          <h1 style={{ margin: 0, fontSize: 22 }}>{chart.symbol} Mum Grafiği</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--muted)' }}>
            Zaman dilimi: {chart.timeframe} · Mum sayısı: {chart.candles.length} {chart.live_filled ? '· canlı dolduruldu' : ''}
          </p>
        </div>
        <ChartControls symbol={symbol} timeframe={timeframe} showVolume={showVolume} showEma={showEma} showRsi={showRsi} showAtr={showAtr} />
        <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
          <LightweightCandles candles={chart.candles} showVolume={showVolume} showEma={showEma} emaPeriod={50} />
        </div>
        {showRsi ? (
          <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
            <IndicatorPanelChart
              title={`RSI 14 · Son ${fmt(lastValue(rsiPoints))}`}
              points={rsiPoints}
              color="#7c3aed"
              guideLines={[{ value: 70, label: 'Aşırı alım' }, { value: 30, label: 'Zayıf bölge' }]}
            />
          </div>
        ) : null}
        {showAtr ? (
          <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
            <IndicatorPanelChart title={`ATR 14 · Son ${fmt(lastValue(atrPoints))}`} points={atrPoints} color="#ea580c" />
          </div>
        ) : null}
      </section>
      <MobileNav active="/charts" />
    </main>
  );
}
