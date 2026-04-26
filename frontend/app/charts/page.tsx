import { MoreVertical, Star } from 'lucide-react';
import { ChartControls } from '@/components/ChartControls';
import { ChartMarkerLegend } from '@/components/ChartMarkerLegend';
import { IndicatorPanelChart } from '@/components/IndicatorPanelChart';
import { LightweightCandles } from '@/components/LightweightCandles';
import { MacdPanelChart } from '@/components/MacdPanelChart';
import { MobileNav } from '@/components/MobileNav';
import { apiGet } from '@/lib/api';
import { adxLine, atrLine, lastValue, macdPoints, mfiLine, rsiLine } from '@/lib/chart-indicators';

type Candle = { timestamp: string; open: number; high: number; low: number; close: number; volume: number };
type TradeMarker = { kind?: 'trade' | 'news' | 'whale'; time: string; position: 'aboveBar' | 'belowBar' | 'inBar'; shape: 'arrowUp' | 'arrowDown' | 'circle' | 'square'; text: string; color: string; title?: string; sentiment?: string; impact_score?: number; event_type?: string; score?: number; notional?: number; price?: number };
type PriceLine = { price: number; title: string; color: string; lineStyle?: 'solid' | 'dashed' };
type ChartResponse = { symbol: string; timeframe: string; candles: Candle[]; live_filled?: boolean; overlays?: { markers?: TradeMarker[]; price_lines?: PriceLine[]; counts?: { trade?: number; news?: number; whale?: number } } };
type PageProps = { searchParams?: Promise<Record<string, string | string[] | undefined>> };

function first(value: string | string[] | undefined, fallback: string) { if (Array.isArray(value)) return value[0] ?? fallback; return value ?? fallback; }
function boolParam(value: string | string[] | undefined, fallback: boolean) { const raw = first(value, String(fallback)); return raw !== 'false'; }
function fmt(value: number | null) { if (value === null) return '—'; return value.toFixed(2); }
function filterMarkers(markers: TradeMarker[], showTrade: boolean, showNews: boolean, showWhale: boolean) { return markers.filter((marker) => { if (marker.kind === 'news') return showNews; if (marker.kind === 'whale') return showWhale; return showTrade; }); }

async function getChart(symbol: string, timeframe: string): Promise<ChartResponse> {
  try { return await apiGet<ChartResponse>(`/api/chart/${symbol}/${timeframe}?limit=300`); }
  catch { return { symbol: symbol.replace('USDT', '/USDT'), timeframe, candles: [] }; }
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
  const latest = chart.candles.at(-1);
  const previous = chart.candles.at(-2);
  const change = latest && previous ? latest.close - previous.close : 0;
  const changePct = latest && previous ? (change / Math.max(previous.close, 1)) * 100 : 0;
  const rsiPoints = rsiLine(chart.candles, 14);
  const atrPoints = atrLine(chart.candles, 14);
  const macd = macdPoints(chart.candles, 12, 26, 9);
  const adxPoints = adxLine(chart.candles, 14);
  const mfiPoints = mfiLine(chart.candles, 14);
  const visibleMarkers = filterMarkers(chart.overlays?.markers ?? [], showTradeMarkers, showNewsMarkers, showWhaleMarkers);
  const counts = chart.overlays?.counts ?? {};

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <h1 className="page-title">Grafikler</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <Star size={21} color="var(--text)" />
          <MoreVertical size={22} color="var(--text)" />
        </div>
      </header>

      <section className="card" style={{ display: 'grid', gap: 10, padding: 10 }}>
        <ChartControls
          symbol={symbol} timeframe={timeframe} showVolume={showVolume} showEma={showEma} showBollinger={showBollinger} showVwap={showVwap} showRsi={showRsi} showAtr={showAtr} showMacd={showMacd} showAdx={showAdx} showMfi={showMfi} showTradeMarkers={showTradeMarkers} showNewsMarkers={showNewsMarkers} showWhaleMarkers={showWhaleMarkers}
        />
        <div style={{ padding: '4px 4px 0' }}>
          <b style={{ fontSize: 13 }}>{chart.symbol} · {chart.timeframe} · Binance</b>
          <div style={{ marginTop: 4, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', fontSize: 11, fontWeight: 800 }}>
            <span style={{ color: change >= 0 ? 'var(--good)' : 'var(--bad)' }}>{latest ? latest.close.toLocaleString('tr-TR', { maximumFractionDigits: 2 }) : '—'}</span>
            <span style={{ color: change >= 0 ? 'var(--good)' : 'var(--bad)' }}>{change >= 0 ? '+' : ''}{change.toFixed(2)} ({changePct.toFixed(2)}%)</span>
            <span style={{ color: 'var(--muted)' }}>İşlem {counts.trade ?? 0}</span>
            <span style={{ color: 'var(--muted)' }}>Haber {counts.news ?? 0}</span>
            <span style={{ color: 'var(--muted)' }}>Balina {counts.whale ?? 0}</span>
          </div>
        </div>
        <div style={{ borderRadius: 14, background: '#fff', border: '1px solid var(--border)', overflow: 'hidden', padding: 4 }}>
          <LightweightCandles candles={chart.candles} showVolume={showVolume} showEma={showEma} showBollinger={showBollinger} showVwap={showVwap} emaPeriod={50} markers={visibleMarkers} priceLines={chart.overlays?.price_lines ?? []} />
        </div>
      </section>

      <div style={{ display: 'grid', gap: 10, marginTop: 10 }}>
        <ChartMarkerLegend markers={visibleMarkers} />
        {showRsi ? <div className="card" style={{ padding: 8 }}><IndicatorPanelChart title={`RSI 14 · ${fmt(lastValue(rsiPoints))}`} points={rsiPoints} color="#7c3aed" guideLines={[{ value: 70, label: 'Üst' }, { value: 30, label: 'Alt' }]} /></div> : null}
        {showMacd ? <div className="card" style={{ padding: 8 }}><MacdPanelChart points={macd} /></div> : null}
        {showAtr ? <div className="card" style={{ padding: 8 }}><IndicatorPanelChart title={`ATR 14 · ${fmt(lastValue(atrPoints))}`} points={atrPoints} color="#ef4444" /></div> : null}
        {showAdx ? <div className="card" style={{ padding: 8 }}><IndicatorPanelChart title={`ADX 14 · ${fmt(lastValue(adxPoints))}`} points={adxPoints} color="#16a34a" guideLines={[{ value: 25, label: 'Trend' }]} /></div> : null}
        {showMfi ? <div className="card" style={{ padding: 8 }}><IndicatorPanelChart title={`MFI 14 · ${fmt(lastValue(mfiPoints))}`} points={mfiPoints} color="#7c3aed" guideLines={[{ value: 80, label: 'Üst' }, { value: 20, label: 'Alt' }]} /></div> : null}
      </div>

      <MobileNav active="/charts" />
    </main>
  );
}
