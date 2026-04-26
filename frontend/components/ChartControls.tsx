'use client';

import { BarChart3, Bitcoin, CandlestickChart, Settings2 } from 'lucide-react';

type Props = {
  symbol: string;
  timeframe: string;
  showVolume: boolean;
  showEma: boolean;
  showBollinger: boolean;
  showVwap: boolean;
  showRsi: boolean;
  showAtr: boolean;
  showMacd: boolean;
  showAdx: boolean;
  showMfi: boolean;
  showTradeMarkers: boolean;
  showNewsMarkers: boolean;
  showWhaleMarkers: boolean;
};

const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'];
const timeframes = ['1h', '1d', '1w'];

function buildUrl(next: Partial<Props>, current: Props) {
  const params = new URLSearchParams();
  params.set('symbol', next.symbol ?? current.symbol);
  params.set('timeframe', next.timeframe ?? current.timeframe);
  params.set('volume', String(next.showVolume ?? current.showVolume));
  params.set('ema', String(next.showEma ?? current.showEma));
  params.set('bb', String(next.showBollinger ?? current.showBollinger));
  params.set('vwap', String(next.showVwap ?? current.showVwap));
  params.set('rsi', String(next.showRsi ?? current.showRsi));
  params.set('atr', String(next.showAtr ?? current.showAtr));
  params.set('macd', String(next.showMacd ?? current.showMacd));
  params.set('adx', String(next.showAdx ?? current.showAdx));
  params.set('mfi', String(next.showMfi ?? current.showMfi));
  params.set('tradeMarkers', String(next.showTradeMarkers ?? current.showTradeMarkers));
  params.set('newsMarkers', String(next.showNewsMarkers ?? current.showNewsMarkers));
  params.set('whaleMarkers', String(next.showWhaleMarkers ?? current.showWhaleMarkers));
  return `/charts?${params.toString()}`;
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (checked: boolean) => void }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginTop: 9, color: 'var(--text)', fontSize: 12, fontWeight: 800 }}>
      <span>{label}</span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} style={{ width: 17, height: 17, accentColor: 'var(--primary)' }} />
    </label>
  );
}

export function ChartControls(props: Props) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1.25fr 0.74fr 36px 36px 36px', gap: 6, alignItems: 'center' }}>
      <label style={{ position: 'relative', minWidth: 0 }}>
        <Bitcoin size={16} color="var(--warning)" style={{ position: 'absolute', left: 9, top: 11, pointerEvents: 'none' }} />
        <select
          value={props.symbol}
          aria-label="Coin seç"
          onChange={(event) => { window.location.href = buildUrl({ symbol: event.target.value }, props); }}
          style={{ width: '100%', border: '1px solid var(--border)', borderRadius: 12, padding: '10px 8px 10px 30px', background: '#fff', fontWeight: 900, fontSize: 12, boxShadow: 'var(--shadow-card)' }}
        >
          {symbols.map((item) => <option key={item} value={item}>{item.replace('USDT', '/USDT')}</option>)}
        </select>
      </label>

      <select
        value={props.timeframe}
        aria-label="Zaman dilimi seç"
        onChange={(event) => { window.location.href = buildUrl({ timeframe: event.target.value }, props); }}
        style={{ width: '100%', border: '1px solid var(--border)', borderRadius: 12, padding: '10px 8px', background: '#fff', fontWeight: 900, fontSize: 12, boxShadow: 'var(--shadow-card)' }}
      >
        {timeframes.map((item) => <option key={item} value={item}>{item}</option>)}
      </select>

      <button title="İndikatörler" style={{ height: 36, border: '1px solid var(--border)', borderRadius: 12, background: '#fff', display: 'grid', placeItems: 'center', color: 'var(--primary)', boxShadow: 'var(--shadow-card)' }} type="button"><BarChart3 size={17} /></button>
      <button title="Mum tipi" style={{ height: 36, border: '1px solid var(--border)', borderRadius: 12, background: '#fff', display: 'grid', placeItems: 'center', color: 'var(--text)', boxShadow: 'var(--shadow-card)' }} type="button"><CandlestickChart size={17} /></button>

      <details style={{ position: 'relative' }}>
        <summary style={{ listStyle: 'none', height: 36, border: '1px solid var(--border)', borderRadius: 12, background: '#fff', cursor: 'pointer', fontWeight: 900, display: 'grid', placeItems: 'center', boxShadow: 'var(--shadow-card)' }}><Settings2 size={17} /></summary>
        <div style={{ position: 'absolute', right: 0, top: 43, zIndex: 10, minWidth: 230, background: '#fff', border: '1px solid var(--border)', borderRadius: 16, boxShadow: '0 18px 48px rgba(35, 56, 92, 0.16)', padding: 12 }}>
          <b style={{ fontSize: 13 }}>Grafik Ayarları</b>
          <p style={{ margin: '6px 0 10px', color: 'var(--muted)', fontSize: 11 }}>İndikatörleri ve işaretleri aç/kapat.</p>
          <Toggle label="EMA 50" checked={props.showEma} onChange={(checked) => { window.location.href = buildUrl({ showEma: checked }, props); }} />
          <Toggle label="VWAP" checked={props.showVwap} onChange={(checked) => { window.location.href = buildUrl({ showVwap: checked }, props); }} />
          <Toggle label="Bollinger Bands" checked={props.showBollinger} onChange={(checked) => { window.location.href = buildUrl({ showBollinger: checked }, props); }} />
          <Toggle label="Hacim" checked={props.showVolume} onChange={(checked) => { window.location.href = buildUrl({ showVolume: checked }, props); }} />
          <hr style={{ border: 0, borderTop: '1px solid var(--border)', margin: '10px 0' }} />
          <Toggle label="RSI 14" checked={props.showRsi} onChange={(checked) => { window.location.href = buildUrl({ showRsi: checked }, props); }} />
          <Toggle label="MACD" checked={props.showMacd} onChange={(checked) => { window.location.href = buildUrl({ showMacd: checked }, props); }} />
          <Toggle label="ATR 14" checked={props.showAtr} onChange={(checked) => { window.location.href = buildUrl({ showAtr: checked }, props); }} />
          <Toggle label="ADX 14" checked={props.showAdx} onChange={(checked) => { window.location.href = buildUrl({ showAdx: checked }, props); }} />
          <Toggle label="MFI 14" checked={props.showMfi} onChange={(checked) => { window.location.href = buildUrl({ showMfi: checked }, props); }} />
          <hr style={{ border: 0, borderTop: '1px solid var(--border)', margin: '10px 0' }} />
          <Toggle label="İşlem işaretleri" checked={props.showTradeMarkers} onChange={(checked) => { window.location.href = buildUrl({ showTradeMarkers: checked }, props); }} />
          <Toggle label="Haber işaretleri" checked={props.showNewsMarkers} onChange={(checked) => { window.location.href = buildUrl({ showNewsMarkers: checked }, props); }} />
          <Toggle label="Balina işaretleri" checked={props.showWhaleMarkers} onChange={(checked) => { window.location.href = buildUrl({ showWhaleMarkers: checked }, props); }} />
        </div>
      </details>
    </div>
  );
}
