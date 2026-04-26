type Signal = {
  symbol?: string;
  decision?: string;
  score?: number;
  created_at?: string;
};

function signalKind(decision?: string) {
  const text = String(decision || '').toLowerCase();
  if (text.includes('al')) return { label: 'AL', className: 'buy' };
  if (text.includes('sat')) return { label: 'SAT', className: 'sell' };
  return { label: 'BEKLE', className: 'wait' };
}

function formatDate(value?: string) {
  if (!value) return '21.05.2025 10:41';
  try {
    return new Intl.DateTimeFormat('tr-TR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

const fallbackSignals: Signal[] = [
  { symbol: 'BTC/USDT', decision: 'AL', score: 0.72 },
  { symbol: 'ETH/USDT', decision: 'BEKLE', score: 0.55 },
  { symbol: 'SOL/USDT', decision: 'SAT', score: 0.68 },
];

export function SignalListCard({ signals }: { signals?: Signal[] }) {
  const rows = signals?.length ? signals.slice(0, 3) : fallbackSignals;
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="card-title">Son Sinyaller</h2>
        <a href="/logs" style={{ color: 'var(--primary)', fontSize: 12, fontWeight: 900 }}>Tümü</a>
      </div>
      <div className="soft-list">
        {rows.map((signal, index) => {
          const kind = signalKind(signal.decision);
          return (
            <article className="signal-row" key={`${signal.symbol}-${index}`}>
              <span className={`signal-badge ${kind.className}`}>{kind.label}</span>
              <div>
                <b style={{ fontSize: 13 }}>{signal.symbol ?? 'BTC/USDT'}</b>
                <div style={{ color: 'var(--muted)', fontSize: 11, marginTop: 2 }}>{formatDate(signal.created_at)}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <b style={{ color: kind.className === 'sell' ? 'var(--bad)' : kind.className === 'buy' ? 'var(--good)' : 'var(--text)' }}>
                  %{Math.round((signal.score ?? 0.55) * 100)}
                </b>
                <div style={{ color: 'var(--muted)', fontSize: 11 }}>Güven</div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
