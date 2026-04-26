import { ChartControls } from '@/components/ChartControls';
import { LightweightCandles } from '@/components/LightweightCandles';
import { MobileNav } from '@/components/MobileNav';
import { apiGet } from '@/lib/api';

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
  const chart = await getChart(symbol, timeframe);

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
        <ChartControls symbol={symbol} timeframe={timeframe} />
        <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
          <LightweightCandles candles={chart.candles} />
        </div>
      </section>
      <MobileNav active="/charts" />
    </main>
  );
}
