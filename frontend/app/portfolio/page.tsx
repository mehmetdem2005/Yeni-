import { MoreVertical, RefreshCcw } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';
import { OpenPositionsCard } from '@/components/OpenPositionsCard';
import { PortfolioRiskCard, PortfolioSummaryCard } from '@/components/PortfolioSummaryCard';
import { TradeHistoryCard } from '@/components/TradeHistoryCard';
import { apiGet } from '@/lib/api';

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
  reason?: string;
  opened_at?: string;
  closed_at?: string;
};

type StatusResponse = {
  wallet?: { cash?: number; starting_balance?: number };
  trade_stats?: { closed_count?: number; open_count?: number; win_rate?: number; total_pnl?: number };
  positions?: Position[];
};

async function getStatus(): Promise<StatusResponse | null> {
  try {
    return await apiGet<StatusResponse>('/api/status');
  } catch {
    return null;
  }
}

function openRiskPct(positions?: Position[]) {
  const open = positions?.filter((item) => item.status === 'OPEN') ?? [];
  const totalRisk = open.reduce((sum, item) => {
    const notional = Number(item.notional ?? 0);
    const entry = Number(item.entry_price ?? 0);
    const stop = Number(item.stop_loss ?? entry);
    if (entry <= 0) return sum;
    return sum + notional * Math.max(0, (entry - stop) / entry);
  }, 0);
  return totalRisk > 0 ? (totalRisk / 10000) * 100 : 0;
}

export default async function PortfolioPage() {
  const status = await getStatus();
  const positions = status?.positions ?? [];

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <h1 className="page-title">Portföy</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a href="/portfolio" style={{ color: 'var(--primary)', display: 'grid', placeItems: 'center' }}><RefreshCcw size={20} /></a>
          <MoreVertical size={22} color="var(--text)" />
        </div>
      </header>

      <div style={{ display: 'grid', gap: 10 }}>
        <PortfolioSummaryCard wallet={status?.wallet} tradeStats={status?.trade_stats} />
        <PortfolioRiskCard openRiskPct={openRiskPct(positions)} />
        <OpenPositionsCard positions={positions} />
        <TradeHistoryCard positions={positions} />
      </div>

      <MobileNav active="/portfolio" />
    </main>
  );
}
