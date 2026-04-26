'use client';

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
  return `/charts?${params.toString()}`;
}

export function ChartControls(props: Props) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, alignItems: 'center' }}>
      <select
        value={props.symbol}
        aria-label="Coin seç"
        onChange={(event) => {
          window.location.href = buildUrl({ symbol: event.target.value }, props);
        }}
        style={{ border: '1px solid var(--border)', borderRadius: 14, padding: '12px 10px', background: '#fff' }}
      >
        {symbols.map((item) => (
          <option key={item} value={item}>{item.replace('USDT', '/USDT')}</option>
        ))}
      </select>
      <select
        value={props.timeframe}
        aria-label="Zaman dilimi seç"
        onChange={(event) => {
          window.location.href = buildUrl({ timeframe: event.target.value }, props);
        }}
        style={{ border: '1px solid var(--border)', borderRadius: 14, padding: '12px 10px', background: '#fff' }}
      >
        {timeframes.map((item) => (
          <option key={item} value={item}>{item}</option>
        ))}
      </select>
      <details style={{ position: 'relative' }}>
        <summary style={{ listStyle: 'none', border: '1px solid var(--border)', borderRadius: 14, padding: '12px 14px', background: 'var(--surface-soft)', cursor: 'pointer', fontWeight: 900 }}>⋮</summary>
        <div style={{ position: 'absolute', right: 0, top: 48, zIndex: 10, minWidth: 255, background: '#fff', border: '1px solid var(--border)', borderRadius: 16, boxShadow: 'var(--shadow-soft)', padding: 10 }}>
          <b>Grafik Ayarları</b>
          <p style={{ margin: '8px 0', color: 'var(--muted)', fontSize: 13 }}>Ayarlar URL ile taşınır; sonraki adımda kullanıcı profilinde saklanacak.</p>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showVolume} onChange={(event) => { window.location.href = buildUrl({ showVolume: event.target.checked }, props); }} /> Hacim</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showEma} onChange={(event) => { window.location.href = buildUrl({ showEma: event.target.checked }, props); }} /> EMA 50</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showBollinger} onChange={(event) => { window.location.href = buildUrl({ showBollinger: event.target.checked }, props); }} /> Bollinger Bands</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showVwap} onChange={(event) => { window.location.href = buildUrl({ showVwap: event.target.checked }, props); }} /> VWAP</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showRsi} onChange={(event) => { window.location.href = buildUrl({ showRsi: event.target.checked }, props); }} /> RSI 14</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showAtr} onChange={(event) => { window.location.href = buildUrl({ showAtr: event.target.checked }, props); }} /> ATR 14</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showMacd} onChange={(event) => { window.location.href = buildUrl({ showMacd: event.target.checked }, props); }} /> MACD 12/26/9</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showAdx} onChange={(event) => { window.location.href = buildUrl({ showAdx: event.target.checked }, props); }} /> ADX 14</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" checked={props.showMfi} onChange={(event) => { window.location.href = buildUrl({ showMfi: event.target.checked }, props); }} /> MFI 14</label>
        </div>
      </details>
    </div>
  );
}
