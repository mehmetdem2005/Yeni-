import { Bitcoin, Building2, Ethereum, TriangleAlert } from 'lucide-react';

type NewsRow = {
  title?: string;
  sentiment?: string;
  published_at?: string;
  source?: string;
};

function sentimentMeta(value?: string) {
  const text = String(value || '').toLowerCase();
  if (text.includes('neg')) return { label: 'Negatif', color: 'var(--bad)', bg: 'var(--bad-soft)', Icon: TriangleAlert };
  if (text.includes('pos')) return { label: 'Pozitif', color: 'var(--good)', bg: 'var(--good-soft)', Icon: Bitcoin };
  return { label: 'Nötr', color: 'var(--muted)', bg: 'var(--surface-soft)', Icon: Building2 };
}

function formatAge(value?: string) {
  if (!value) return '2 dk önce';
  const delta = Date.now() - new Date(value).getTime();
  if (!Number.isFinite(delta)) return 'az önce';
  const minutes = Math.max(1, Math.round(delta / 60000));
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} saat önce`;
  return `${Math.round(hours / 24)} gün önce`;
}

const fallbackNews: NewsRow[] = [
  { title: 'Bitcoin ETF’lerine güçlü girişler devam ediyor', sentiment: 'positive' },
  { title: 'Ethereum güncellemesi sağlıklı ilerliyor', sentiment: 'positive' },
  { title: 'Fed yetkililerinden faiz mesajı: Veriler belirleyici olacak', sentiment: 'neutral' },
  { title: 'ABD’de enflasyon verisi beklentilerin üzerinde geldi', sentiment: 'negative' },
];

export function NewsFeedCard({ news }: { news?: NewsRow[] }) {
  const rows = news?.length ? news.slice(0, 4) : fallbackNews;
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="card-title">Haberler</h2>
        <a href="/news" style={{ color: 'var(--primary)', fontSize: 12, fontWeight: 900 }}>Tümü ›</a>
      </div>
      <div className="soft-list">
        {rows.map((row, index) => {
          const meta = sentimentMeta(row.sentiment);
          const Icon = meta.Icon;
          return (
            <article key={`${row.title}-${index}`} style={{ display: 'grid', gridTemplateColumns: '38px 1fr auto', gap: 10, alignItems: 'center', padding: '9px 0', borderBottom: index === rows.length - 1 ? 0 : '1px solid var(--border)' }}>
              <span style={{ display: 'grid', placeItems: 'center', width: 34, height: 34, borderRadius: 13, color: meta.color, background: meta.bg }}><Icon size={18} /></span>
              <div>
                <p style={{ margin: 0, fontSize: 12, fontWeight: 800, lineHeight: 1.32 }}>{row.title}</p>
                <small style={{ color: 'var(--muted)' }}>{formatAge(row.published_at)}</small>
              </div>
              <span style={{ color: meta.color, background: meta.bg, borderRadius: 10, padding: '6px 8px', fontSize: 11, fontWeight: 900 }}>{meta.label}</span>
            </article>
          );
        })}
      </div>
      <a href="/news" style={{ color: 'var(--primary)', fontSize: 12, fontWeight: 900, textAlign: 'center' }}>Tüm Haberleri Gör ›</a>
    </section>
  );
}
