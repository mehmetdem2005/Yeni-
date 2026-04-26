import { ShieldCheck, TrendingDown, TrendingUp, WalletCards } from 'lucide-react';

type TradeStats = {
  closed_count?: number;
  open_count?: number;
  win_rate?: number;
  total_pnl?: number;
};

type Wallet = {
  cash?: number;
  starting_balance?: number;
};

function money(value?: number) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '0.00';
  return Number(value).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function pct(value?: number) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return '%0';
  return `%${Math.round(Number(value) * 100)}`;
}

export function PortfolioSummaryCard({ wallet, tradeStats }: { wallet?: Wallet; tradeStats?: TradeStats }) {
  const pnl = Number(tradeStats?.total_pnl ?? 0);
  const pnlPositive = pnl >= 0;
  const starting = Number(wallet?.starting_balance ?? 10000);
  const cash = Number(wallet?.cash ?? starting);
  const equityChange = starting > 0 ? (cash + pnl - starting) / starting : 0;
  const TrendIcon = pnlPositive ? TrendingUp : TrendingDown;

  return (
    <section className="card" style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 11, fontWeight: 900 }}>PAPER TRADE PORTFÖY</div>
          <h2 className="card-title" style={{ marginTop: 3 }}>Sanal Hesap Özeti</h2>
        </div>
        <span className="icon-tile"><WalletCards size={19} /></span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <div style={{ borderRadius: 15, background: 'var(--surface-soft)', padding: 11 }}>
          <div className="kpi-label">Sanal Nakit</div>
          <div className="kpi-value" style={{ fontSize: 19 }}>{money(cash)}</div>
          <small style={{ color: 'var(--muted)', fontWeight: 800 }}>USDT</small>
        </div>
        <div style={{ borderRadius: 15, background: pnlPositive ? 'var(--good-soft)' : 'var(--bad-soft)', padding: 11 }}>
          <div className="kpi-label">Toplam K/Z</div>
          <div className="kpi-value" style={{ fontSize: 19, color: pnlPositive ? 'var(--good)' : 'var(--bad)' }}>{pnlPositive ? '+' : '-'}{money(Math.abs(pnl))}</div>
          <small style={{ color: pnlPositive ? 'var(--good)' : 'var(--bad)', fontWeight: 900 }}>{pnlPositive ? '+' : ''}{(equityChange * 100).toFixed(2)}%</small>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        <div style={{ textAlign: 'center', borderRadius: 14, border: '1px solid var(--border)', padding: 9 }}>
          <b>{tradeStats?.open_count ?? 0}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Açık</div>
        </div>
        <div style={{ textAlign: 'center', borderRadius: 14, border: '1px solid var(--border)', padding: 9 }}>
          <b>{tradeStats?.closed_count ?? 0}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Kapalı</div>
        </div>
        <div style={{ textAlign: 'center', borderRadius: 14, border: '1px solid var(--border)', padding: 9 }}>
          <b>{pct(tradeStats?.win_rate)}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Başarı</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: 'var(--surface-soft)' }}>
        <span style={{ display: 'grid', placeItems: 'center', color: pnlPositive ? 'var(--good)' : 'var(--bad)' }}><TrendIcon size={18} /></span>
        <p style={{ margin: 0, color: 'var(--muted)', fontSize: 12, lineHeight: 1.4 }}>
          Bu sayfa gerçek para değil, paper-trade sonuçlarını gösterir. Canlı paraya geçiş için test kriterlerinin tamamı yeşil olmalıdır.
        </p>
      </div>
    </section>
  );
}

export function PortfolioRiskCard({ openRiskPct = 0.0 }: { openRiskPct?: number }) {
  const safe = openRiskPct <= 1;
  return (
    <section className="card" style={{ display: 'grid', gridTemplateColumns: '38px 1fr auto', gap: 10, alignItems: 'center' }}>
      <span className="icon-tile" style={{ color: safe ? 'var(--good)' : 'var(--bad)', background: safe ? 'var(--good-soft)' : 'var(--bad-soft)' }}><ShieldCheck size={19} /></span>
      <div>
        <h2 className="card-title">Portföy Risk Güvenliği</h2>
        <p className="card-muted" style={{ margin: '5px 0 0' }}>Toplam açık risk sınırı: %1.0</p>
      </div>
      <b style={{ color: safe ? 'var(--good)' : 'var(--bad)' }}>%{openRiskPct.toFixed(2)}</b>
    </section>
  );
}
