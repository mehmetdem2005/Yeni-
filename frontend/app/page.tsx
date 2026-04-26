import { ChartNoAxesCombined, ShieldCheck, TrendingUp, WalletCards } from 'lucide-react';
import { AiSummaryCard } from '@/components/AiSummaryCard';
import { AutomationStatusCard } from '@/components/AutomationStatusCard';
import { DashboardActionStrip } from '@/components/DashboardActionStrip';
import { EquityPreviewCard } from '@/components/EquityPreviewCard';
import { MobileNav } from '@/components/MobileNav';
import { SignalListCard } from '@/components/SignalListCard';
import { apiGet } from '@/lib/api';

type StatusResponse = {
  db_rows?: number;
  latest_signals?: Array<{ symbol?: string; decision?: string; score?: number; created_at?: string }>;
  trade_stats?: { closed_count?: number; open_count?: number; win_rate?: number; total_pnl?: number };
  wallet?: { cash?: number; starting_balance?: number };
  system_confidence?: { system_confidence?: number; status?: string; explanation?: string };
  database?: { backend?: string; note?: string };
  automation?: { running?: boolean };
};

function pct(value?: number) {
  if (value === undefined || value === null) return '%0';
  return `%${Math.round(value * 100)}`;
}

function money(value?: number) {
  if (value === undefined || value === null) return '10,000.00';
  return Number(value).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function getStatus(): Promise<StatusResponse | null> {
  try {
    return await apiGet<StatusResponse>('/api/status');
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const status = await getStatus();
  const confidence = status?.system_confidence?.system_confidence ?? 0.74;
  const pnl = status?.trade_stats?.total_pnl ?? 125.64;
  const pnlPositive = pnl >= 0;
  const openCount = status?.trade_stats?.open_count ?? 2;
  const running = Boolean(status?.automation?.running);

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 0 }}>
          <h1 className="page-title">Kripto Spot Botu</h1>
          <span className="chip">Paper Trade</span>
        </div>
        <div className="confidence-badge">
          <span>Toplam Güven</span>
          <b>{pct(confidence)}</b>
        </div>
      </header>

      <div style={{ display: 'grid', gap: 10 }}>
        <AiSummaryCard text={status?.system_confidence?.explanation} />

        <section className="compact-grid">
          <article className="card kpi-card">
            <div className="kpi-label">Sanal Bakiye</div>
            <div className="kpi-value">{money(status?.wallet?.cash)}</div>
            <div className="kpi-foot"><span>USDT</span><span className="icon-tile"><WalletCards size={18} /></span></div>
          </article>

          <article className="card kpi-card">
            <div className="kpi-label">Bugünkü Kâr/Zarar</div>
            <div className="kpi-value" style={{ color: pnlPositive ? 'var(--good)' : 'var(--bad)' }}>{pnlPositive ? '+' : ''}{money(Math.abs(pnl))}</div>
            <div className="kpi-foot"><span>USDT</span><span style={{ color: pnlPositive ? 'var(--good)' : 'var(--bad)', fontWeight: 900 }}>+1,26%</span><span className="icon-tile" style={{ color: 'var(--good)', background: 'var(--good-soft)' }}><TrendingUp size={18} /></span></div>
          </article>

          <article className="card kpi-card">
            <div className="kpi-label">Açık Pozisyon</div>
            <div className="kpi-value">{openCount}</div>
            <div className="kpi-foot"><span>Toplam</span><span className="icon-tile"><ChartNoAxesCombined size={18} /></span></div>
          </article>

          <article className="card kpi-card">
            <div className="kpi-label">Sistem Durumu</div>
            <div className="kpi-value" style={{ color: running ? 'var(--good)' : 'var(--muted)', fontSize: 18 }}>{running ? 'Çalışıyor' : 'Beklemede'}</div>
            <div className="kpi-foot"><span>{running ? 'Otomatik' : 'Manuel'}</span><span className="icon-tile" style={{ color: running ? 'var(--good)' : 'var(--primary)', background: running ? 'var(--good-soft)' : 'var(--primary-soft)' }}><ShieldCheck size={18} /></span></div>
          </article>
        </section>

        <DashboardActionStrip />
        <AutomationStatusCard />
        <EquityPreviewCard cash={status?.wallet?.cash ?? 10000} pnl={pnl} />
        <SignalListCard signals={status?.latest_signals} />
      </div>

      <MobileNav active="/" />
    </main>
  );
}
