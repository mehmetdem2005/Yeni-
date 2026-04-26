import { ArrowDownRight, ArrowUpRight, CircleDollarSign } from 'lucide-react';

type Position = {
  id?: string;
  symbol?: string;
  status?: string;
  entry_price?: number;
  close_price?: number;
  qty?: number;
  notional?: number;
  stop_loss?: number;
  take_profit?: number;
  pnl?: number;
  opened_at?: string;
};

function money(value?: number) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '—';
  return Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 2 });
}

function time(value?: string) {
  if (!value) return 'az önce';
  try {
    return new Intl.DateTimeFormat('tr-TR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }).format(new Date(value));
  } catch {
    return value;
  }
}

const fallback: Position[] = [
  { symbol: 'BTC/USDT', status: 'OPEN', entry_price: 68120.5, notional: 250, stop_loss: 66980, take_profit: 71340, opened_at: '' },
  { symbol: 'ETH/USDT', status: 'OPEN', entry_price: 3442.2, notional: 180, stop_loss: 3375, take_profit: 3615, opened_at: '' },
];

export function OpenPositionsCard({ positions }: { positions?: Position[] }) {
  const open = (positions?.filter((item) => item.status === 'OPEN') ?? []);
  const rows = open.length ? open : fallback;
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 className="card-title">Açık Pozisyonlar</h2>
        <span style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 900 }}>{rows.length} adet</span>
      </div>
      <div className="soft-list">
        {rows.map((pos, index) => (
          <article key={`${pos.id ?? pos.symbol}-${index}`} style={{ border: '1px solid var(--border)', borderRadius: 16, padding: 11, display: 'grid', gap: 9, background: '#fff' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                <span className="icon-tile" style={{ color: 'var(--good)', background: 'var(--good-soft)' }}><CircleDollarSign size={18} /></span>
                <div>
                  <b style={{ fontSize: 13 }}>{pos.symbol}</b>
                  <div style={{ color: 'var(--muted)', fontSize: 11 }}>Açılış: {time(pos.opened_at)}</div>
                </div>
              </div>
              <span style={{ color: 'var(--good)', background: 'var(--good-soft)', borderRadius: 11, padding: '6px 8px', fontSize: 11, fontWeight: 950 }}>LONG</span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 7 }}>
              <div style={{ background: 'var(--surface-soft)', borderRadius: 13, padding: 8 }}><small style={{ color: 'var(--muted)' }}>Giriş</small><br /><b>{money(pos.entry_price)}</b></div>
              <div style={{ background: 'var(--bad-soft)', borderRadius: 13, padding: 8 }}><small style={{ color: 'var(--bad)' }}>SL</small><br /><b>{money(pos.stop_loss)}</b></div>
              <div style={{ background: 'var(--good-soft)', borderRadius: 13, padding: 8 }}><small style={{ color: 'var(--good)' }}>TP</small><br /><b>{money(pos.take_profit)}</b></div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>
              <span><ArrowUpRight size={13} /> Notional: {money(pos.notional)} USDT</span>
              <span><ArrowDownRight size={13} /> Risk kontrollü</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
