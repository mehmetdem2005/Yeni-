import { MoreVertical, Sparkles } from 'lucide-react';
import { AssistantChatClient } from '@/components/AssistantChatClient';
import { AssistantSystemContextCard } from '@/components/AssistantSystemContextCard';
import { MobileNav } from '@/components/MobileNav';
import { apiGet } from '@/lib/api';

type StatusResponse = {
  db_rows?: number;
  wallet?: { cash?: number };
  trade_stats?: { open_count?: number; closed_count?: number; win_rate?: number; total_pnl?: number };
  system_confidence?: { system_confidence?: number; status?: string };
};

async function getStatus(): Promise<StatusResponse | null> {
  try {
    return await apiGet<StatusResponse>('/api/status');
  } catch {
    return null;
  }
}

export default async function AssistantPage() {
  const status = await getStatus();

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <div>
          <h1 className="page-title">AI Asistan</h1>
          <p style={{ margin: '4px 0 0', color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>
            Sistemi sade Türkçe ile açıklar
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Sparkles size={20} color="var(--primary)" />
          <MoreVertical size={22} color="var(--text)" />
        </div>
      </header>

      <div style={{ display: 'grid', gap: 10 }}>
        <AssistantSystemContextCard status={status} />
        <AssistantChatClient />
      </div>

      <MobileNav active="/assistant" />
    </main>
  );
}
