import { MoreVertical, RefreshCcw } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';
import { NewsFilterTabs } from '@/components/NewsFilterTabs';
import { NewsInsightCard } from '@/components/NewsInsightCard';
import { NewsListPanel } from '@/components/NewsListPanel';

type PageProps = {
  searchParams?: Promise<Record<string, string | string[] | undefined>>;
};

function first(value: string | string[] | undefined, fallback: string) {
  if (Array.isArray(value)) return value[0] ?? fallback;
  return value ?? fallback;
}

function normalizeFilter(value: string): 'all' | 'positive' | 'neutral' | 'negative' {
  if (value === 'positive' || value === 'neutral' || value === 'negative') return value;
  return 'all';
}

export default async function NewsPage({ searchParams }: PageProps) {
  const params = (await searchParams) ?? {};
  const filter = normalizeFilter(first(params.filter, 'all'));

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <h1 className="page-title">Haberler</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a href="/logs?tab=news" style={{ color: 'var(--primary)', display: 'grid', placeItems: 'center' }}><RefreshCcw size={20} /></a>
          <MoreVertical size={22} color="var(--text)" />
        </div>
      </header>

      <div style={{ display: 'grid', gap: 10 }}>
        <NewsInsightCard />
        <NewsFilterTabs active={filter} />
        <NewsListPanel filter={filter} />
      </div>

      <MobileNav active="/news" />
    </main>
  );
}
