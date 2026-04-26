type Props = {
  symbol: string;
  timeframe: string;
};

const symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'];
const timeframes = ['1h', '1d', '1w'];

export function ChartControls({ symbol, timeframe }: Props) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, alignItems: 'center' }}>
      <select
        defaultValue={symbol}
        aria-label="Coin seç"
        onChange={(event) => {
          window.location.href = `/charts?symbol=${event.target.value}&timeframe=${timeframe}`;
        }}
        style={{ border: '1px solid var(--border)', borderRadius: 14, padding: '12px 10px', background: '#fff' }}
      >
        {symbols.map((item) => (
          <option key={item} value={item}>{item.replace('USDT', '/USDT')}</option>
        ))}
      </select>
      <select
        defaultValue={timeframe}
        aria-label="Zaman dilimi seç"
        onChange={(event) => {
          window.location.href = `/charts?symbol=${symbol}&timeframe=${event.target.value}`;
        }}
        style={{ border: '1px solid var(--border)', borderRadius: 14, padding: '12px 10px', background: '#fff' }}
      >
        {timeframes.map((item) => (
          <option key={item} value={item}>{item}</option>
        ))}
      </select>
      <details style={{ position: 'relative' }}>
        <summary style={{ listStyle: 'none', border: '1px solid var(--border)', borderRadius: 14, padding: '12px 14px', background: 'var(--surface-soft)', cursor: 'pointer', fontWeight: 900 }}>⋮</summary>
        <div style={{ position: 'absolute', right: 0, top: 48, zIndex: 10, minWidth: 210, background: '#fff', border: '1px solid var(--border)', borderRadius: 16, boxShadow: 'var(--shadow-soft)', padding: 10 }}>
          <b>Grafik Ayarları</b>
          <p style={{ margin: '8px 0', color: 'var(--muted)', fontSize: 13 }}>Sonraki adımda buraya EMA, RSI, ATR, hacim ve renk ayarları bağlanacak.</p>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" defaultChecked /> Hacim</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" /> EMA</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" /> RSI</label>
          <label style={{ display: 'block', marginTop: 8 }}><input type="checkbox" /> ATR</label>
        </div>
      </details>
    </div>
  );
}
