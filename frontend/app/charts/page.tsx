import { MoreVertical } from 'lucide-react';
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
};

async function getChart(): Promise<ChartResponse> {
  try {
    return await apiGet<ChartResponse>('/api/chart/BTCUSDT/1h?limit=300');
  } catch {
    return { symbol: 'BTC/USDT', timeframe: '1h', candles: [] };
  }
}

export default async function ChartsPage() {
  const chart = await getChart();

  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>GRAFİKLER</div>
            <h1 style={{ margin: 0, fontSize: 22 }}>{chart.symbol} Mum Grafiği</h1>
            <p style={{ margin: '4px 0 0', color: 'var(--muted)' }}>Zaman dilimi: {chart.timeframe} · Mum sayısı: {chart.candles.length}</p>
          </div>
          <button aria-label="Grafik ayarları" style={{ border: 0, background: 'var(--surface-soft)', borderRadius: 14, padding: 10 }}>
            <MoreVertical size={20} />
          </button>
        </div>
        <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
          <LightweightCandles candles={chart.candles} />
        </div>
      </section>
      <MobileNav active="/charts" />
    </main>
  );
}
