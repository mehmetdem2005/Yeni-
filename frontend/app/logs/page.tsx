import { Bell, MoreVertical } from 'lucide-react';
import { AssistantPreviewCard } from '@/components/AssistantPreviewCard';
import { LiveFlowTabs } from '@/components/LiveFlowTabs';
import { LiveLogCard } from '@/components/LiveLogCard';
import { MobileNav } from '@/components/MobileNav';
import { NewsFeedCard } from '@/components/NewsFeedCard';
import { apiGet } from '@/lib/api';

type StatusResponse = {
  logs?: Array<{ created_at?: string; channel?: string; level?: string; message?: string; user_explanation?: string }>;
};

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined, fallback: string) {
  if (Array.isArray(value)) return value[0] ?? fallback;
  return value ?? fallback;
}

async function getStatus(): Promise<StatusResponse | null> {
  try {
    return await apiGet<StatusResponse>('/api/status');
  } catch {
    return null;
  }
}

export default async function LogsPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const tab = first(params.tab, 'logs') as 'logs' | 'news' | 'assistant';
  const status = await getStatus();

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <h1 className="page-title">Canlı Akış</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Bell size={20} color="var(--text)" />
          <MoreVertical size={22} color="var(--text)" />
        </div>
      </header>

      <div style={{ display: 'grid', gap: 10 }}>
        <LiveFlowTabs active={tab} />
        {tab === 'logs' ? <LiveLogCard logs={status?.logs} /> : null}
        {tab === 'news' ? <NewsFeedCard /> : null}
        {tab === 'assistant' ? <AssistantPreviewCard /> : null}
      </div>

      <MobileNav active="/logs" />
    </main>
  );
}
