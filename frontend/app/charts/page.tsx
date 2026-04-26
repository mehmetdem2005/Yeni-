import { ChartControls } from '@/components/ChartControls';
import { ChartMarkerLegend } from '@/components/ChartMarkerLegend';
import { IndicatorPanelChart } from '@/components/IndicatorPanelChart';
import { LightweightCandles } from '@/components/LightweightCandles';
import { MacdPanelChart } from '@/components/MacdPanelChart';
import { MobileNav } from '@/components/MobileNav';
import { apiGet } from '@/lib/api';
import { adxLine, atrLine, lastValue, macdPoints, mfiLine, rsiLine } from '@/lib/chart-indicators';

type Candle = {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type TradeMarker = {
  kind?: 'trade' | 'news' | 'whale';
  time: string;
  position: 'aboveBar' | 'belowBar' | 'inBar';
  shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square';
  text: string;
  color: string;
  title?: string;
  sentiment?: string;
  impact_score?: number;
  event_type?: string;
  score?: number;
  notional?: number;
  price?: number;
};

type PriceLine = {
  price: number;
  title: string;
  color: string;
  lineStyle?: 'solid' | 'dashed';
};

type ChartResponse = {
  symbol: string;
  timeframe: string;
  candles: Candle[];
  live_filled?: boolean;
  overlays?: {
    markers?: TradeMarker[];
    price_lines?: PriceLine[];
    counts?: { trade?: number; news?: number; whale?: number };
  };
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

function filterMarkers(markers: TradeMarker[], showTrade: boolean, showNews: boolean, showWhale: boolean) {
  return markers.filter((marker) => {
    if (marker.kind === 'news') return showNews;
    if (marker.kind === 'whale') return showWhale;
    return showTrade;
  });
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
  const showBollinger = boolParam(params.bb, false);
  const showVwap = boolParam(params.vwap, false);
  const showRsi = boolParam(params.rsi, true);
  const showAtr = boolParam(params.atr, true);
  const showMacd = boolParam(params.macd, true);
  const showAdx = boolParam(params.adx, false);
  const showMfi = boolParam(params.mfi, false);
  const showTradeMarkers = boolParam(params.tradeMarkers, true);
  const showNewsMarkers = boolParam(params.newsMarkers, true);
  const showWhaleMarkers = boolParam(params.whaleMarkers, true);
  const chart = await getChart(symbol, timeframe);
  const rsiPoints = rsiLine(chart.candles, 14);
  const atrPoints = atrLine(chart.candles, 14);
  const macd = macdPoints(chart.candles, 12, 26, 9);
  const adxPoints = adxLine(chart.candles, 14);
  const mfiPoints = mfiLine(chart.candles, 14);
  const visibleMarkers = filterMarkers(chart.overlays?.markers ?? [], showTradeMarkers, showNewsMarkers, showWhaleMarkers);
  const counts = chart.overlays?.counts ?? {};

  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 12 }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>GRAFİKLER</div>
          <h1 style={{ margin: 0, fontSize: 22 }}>{chart.symbol} Mum Grafiği</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--muted)' }}>
            Zaman dilimi: {chart.timeframe} · Mum sayısı: {chart.candles.length} {chart.live_filled ? '· canlı dolduruldu' : ''}
            {visibleMarkers.length ? ` · ${visibleMarkers.length} görünür işaret` : ''}
          </p>
          <p style={{ margin: '4px 0 0', color: 'var(--muted)', fontSize: 12 }}>
            İşlem: {counts.trade ?? 0} · Haber: {counts.news ?? 0} · Balina: {counts.whale ?? 0}
          </p>
        </div>
        <ChartControls
          symbol={symbol}
          timeframe={timeframe}
          showVolume={showVolume}
          showEma={showEma}
          showBollinger={showBollinger}
          showVwap={showVwap}
          showRsi={showRsi}
          showAtr={showAtr}
          showMacd={showMacd}
          showAdx={showAdx}
          showMfi={showMfi}
          showTradeMarkers={showTradeMarkers}
          showNewsMarkers={showNewsMarkers}
          showWhaleMarkers={showWhaleMarkers}
        />
        <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
          <LightweightCandles
            candles={chart.candles}
            showVolume={showVolume}
            showEma={showEma}
            showBollinger={showBollinger}
            showVwap={showVwap}
            emaPeriod={50}
            markers={visibleMarkers}
            priceLines={chart.overlays?.price_lines ?? []}
          />
        </div>
        <ChartMarkerLegend markers={visibleMarkers} />
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
        {showMacd ? (
          <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
            <MacdPanelChart points={macd} />
          </div>
        ) : null}
        {showAdx ? (
          <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
            <IndicatorPanelChart title={`ADX 14 · Son ${fmt(lastValue(adxPoints))}`} points={adxPoints} color="#0f766e" guideLines={[{ value: 25, label: 'Güçlü trend' }]} />
          </div>
        ) : null}
        {showMfi ? (
          <div style={{ borderRadius: 18, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 8 }}>
            <IndicatorPanelChart title={`MFI 14 · Son ${fmt(lastValue(mfiPoints))}`} points={mfiPoints} color="#0891b2" guideLines={[{ value: 80, label: 'Para aşırı giriş' }, { value: 20, label: 'Para zayıf' }]} />
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
