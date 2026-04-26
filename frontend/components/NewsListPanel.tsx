import { Bitcoin, Building2, ExternalLink, TriangleAlert } from 'lucide-react';

type NewsRow = {
  title?: string;
  source?: string;
  sentiment?: string;
  sentiment_score?: number;
  impact_score?: number;
  published_at?: string;
  link?: string;
};

function sentimentMeta(value?: string, score?: number) {
  const text = String(value || '').toLowerCase();
  if (text.includes('neg') || Number(score ?? 0) < -0.15) return { label: 'Negatif', color: 'var(--bad)', bg: 'var(--bad-soft)', Icon: TriangleAlert };
  if (text.includes('pos') || Number(score ?? 0) > 0.15) return { label: 'Pozitif', color: 'var(--good)', bg: 'var(--good-soft)', Icon: Bitcoin };
  return { label: 'Nötr', color: 'var(--muted)', bg: 'var(--surface-soft)', Icon: Building2 };
}

function formatAge(value?: string) {
  if (!value) return 'az önce';
  const delta = Date.now() - new Date(value).getTime();
  if (!Number.isFinite(delta)) return 'az önce';
  const minutes = Math.max(1, Math.round(delta / 60000));
  if (minutes < 60) return `${minutes} dk önce`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} saat önce`;
  return `${Math.round(hours / 24)} gün önce`;
}

const fallbackNews: NewsRow[] = [
  { title: 'Bitcoin ETF’lerine güçlü girişler devam ediyor', source: 'Piyasa Akışı', sentiment: 'positive', sentiment_score: 0.44, impact_score: 0.62 },
  { title: 'Ethereum güncellemesi sağlıklı ilerliyor', source: 'Zincir Haberleri', sentiment: 'positive', sentiment_score: 0.31, impact_score: 0.48 },
  { title: 'Fed yetkililerinden faiz mesajı: Veriler belirleyici olacak', source: 'Makro', sentiment: 'neutral', sentiment_score: 0.02, impact_score: 0.22 },
  { title: 'ABD’de enflasyon verisi beklentilerin üzerinde geldi', source: 'Makro', sentiment: 'negative', sentiment_score: -0.34, impact_score: 0.55 },
];

function passesFilter(row: NewsRow, filter: string) {
  if (filter === 'all') return true;
  const meta = sentimentMeta(row.sentiment, row.sentiment_score);
  return meta.label.toLowerCase() === filter.replace('positive', 'pozitif').replace('neutral', 'nötr').replace('negative', 'negatif');
}

export function NewsListPanel({ news, filter }: { news?: NewsRow[]; filter: 'all' | 'positive' | 'neutral' | 'negative' }) {
  const rows = (news?.length ? news : fallbackNews).filter((row) => passesFilter(row, filter));
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 className="card-title">Haber Akışı</h2>
        <span style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 900 }}>{rows.length} kayıt</span>
      </div>
      <div className="soft-list">
        {rows.map((row, index) => {
          const meta = sentimentMeta(row.sentiment, row.sentiment_score);
          const Icon = meta.Icon;
          return (
            <article key={`${row.title}-${index}`} style={{ display: 'grid', gridTemplateColumns: '38px 1fr', gap: 10, alignItems: 'start', padding: '11px 0', borderBottom: index === rows.length - 1 ? 0 : '1px solid var(--border)' }}>
              <span style={{ display: 'grid', placeItems: 'center', width: 34, height: 34, borderRadius: 13, color: meta.color, background: meta.bg }}><Icon size={18} /></span>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: 8 }}>
                  <p style={{ margin: 0, fontSize: 13, fontWeight: 850, lineHeight: 1.35 }}>{row.title}</p>
                  <span style={{ color: meta.color, background: meta.bg, borderRadius: 10, padding: '5px 7px', fontSize: 10, fontWeight: 950, whiteSpace: 'nowrap' }}>{meta.label}</span>
                </div>
                <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', color: 'var(--muted)', fontSize: 11, fontWeight: 700 }}>
                  <span>{row.source || 'Kaynak'}</span>
                  <span>·</span>
                  <span>{formatAge(row.published_at)}</span>
                  <span>Etki: {Number(row.impact_score ?? 0).toFixed(2)}</span>
                  {row.link ? <ExternalLink size={13} /> : null}
                </div>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
