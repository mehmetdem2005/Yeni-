import { CheckCircle2, Clock3, XCircle } from 'lucide-react';

type Position = {
  id?: string;
  symbol?: string;
  status?: string;
  entry_price?: number;
  close_price?: number;
  pnl?: number;
  reason?: string;
  opened_at?: string;
  closed_at?: string;
};

function money(value?: number) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '—';
  return Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 2 });
}

function time(value?: string) {
  if (!value) return 'bugün';
  try {
    return new Intl.DateTimeFormat('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value));
  } catch {
    return value;
  }
}

const fallback: Position[] = [
  { symbol: 'BTC/USDT', status: 'CLOSED', pnl: 42.35, reason: 'KÂR AL', closed_at: '' },
  { symbol: 'SOL/USDT', status: 'CLOSED', pnl: -18.22, reason: 'ZARAR KES', closed_at: '' },
  { symbol: 'ETH/USDT', status: 'CLOSED', pnl: 21.1, reason: 'ZAMAN', closed_at: '' },
];

export function TradeHistoryCard({ positions }: { positions?: Position[] }) {
  const closed = positions?.filter((item) => item.status === 'CLOSED') ?? [];
  const rows = closed.length ? closed.slice(0, 5) : fallback;
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="card-title">İşlem Geçmişi</h2>
        <a href="/logs?tab=logs" style={{ color: 'var(--primary)', fontSize: 12, fontWeight: 900 }}>Detay ›</a>
      </div>
      <div className="soft-list">
        {rows.map((pos, index) => {
          const pnl = Number(pos.pnl ?? 0);
          const positive = pnl >= 0;
          const Icon = pos.reason === 'ZAMAN' ? Clock3 : positive ? CheckCircle2 : XCircle;
          return (
            <article key={`${pos.id ?? pos.symbol}-${index}`} style={{ display: 'grid', gridTemplateColumns: '36px 1fr auto', gap: 10, alignItems: 'center', padding: '9px 0', borderBottom: index === rows.length - 1 ? 0 : '1px solid var(--border)' }}>
              <span style={{ display: 'grid', placeItems: 'center', width: 34, height: 34, borderRadius: 13, color: positive ? 'var(--good)' : 'var(--bad)', background: positive ? 'var(--good-soft)' : 'var(--bad-soft)' }}><Icon size={18} /></span>
              <div>
                <b style={{ fontSize: 13 }}>{pos.symbol}</b>
                <div style={{ color: 'var(--muted)', fontSize: 11 }}>{pos.reason ?? 'KAPANDI'} · {time(pos.closed_at)}</div>
              </div>
              <b style={{ color: positive ? 'var(--good)' : 'var(--bad)', fontSize: 13 }}>{positive ? '+' : '-'}{money(Math.abs(pnl))}</b>
            </article>
          );
        })}
      </div>
    </section>
  );
}
