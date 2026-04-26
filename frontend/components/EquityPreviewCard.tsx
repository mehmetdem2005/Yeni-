function money(value?: number) {
  if (value === undefined || value === null) return '10,000 USDT';
  return `${Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 0 })} USDT`;
}

export function EquityPreviewCard({ cash, pnl }: { cash?: number; pnl?: number }) {
  const positive = (pnl ?? 0) >= 0;
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 className="card-title">Bakiye Eğrisi</h2>
        <span className="chip" style={{ color: 'var(--text)', background: '#fff', border: '1px solid var(--border)' }}>7 Gün⌄</span>
      </div>
      <div>
        <b style={{ fontSize: 18 }}>{money(cash)}</b>
        <span style={{ marginLeft: 8, color: positive ? 'var(--good)' : 'var(--bad)', fontWeight: 900, fontSize: 12 }}>
          {positive ? '+' : ''}{((pnl ?? 0) / Math.max(cash ?? 10000, 1) * 100).toFixed(2)}%
        </span>
      </div>
      <div className="mini-line-chart" aria-label="Bakiye eğrisi">
        <svg viewBox="0 0 320 170" preserveAspectRatio="none">
          <defs>
            <linearGradient id="equityFill" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#2563eb" stopOpacity="0.22" />
              <stop offset="100%" stopColor="#2563eb" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d="M0 136 L25 121 L45 128 L66 103 L88 92 L110 107 L130 72 L154 88 L174 62 L196 68 L218 51 L240 76 L262 44 L286 36 L320 24 L320 170 L0 170 Z" fill="url(#equityFill)" />
          <path d="M0 136 L25 121 L45 128 L66 103 L88 92 L110 107 L130 72 L154 88 L174 62 L196 68 L218 51 L240 76 L262 44 L286 36 L320 24" fill="none" stroke="#2563eb" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="320" cy="24" r="5" fill="#fff" stroke="#2563eb" strokeWidth="3" />
        </svg>
      </div>
    </section>
  );
}
