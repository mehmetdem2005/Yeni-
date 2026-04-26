type Props = {
  active: 'all' | 'positive' | 'neutral' | 'negative';
};

const tabs = [
  { key: 'all', label: 'Tümü' },
  { key: 'positive', label: 'Pozitif' },
  { key: 'neutral', label: 'Nötr' },
  { key: 'negative', label: 'Negatif' },
] as const;

export function NewsFilterTabs({ active }: Props) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', padding: 3, borderRadius: 14, border: '1px solid var(--border)', background: '#fff', boxShadow: 'var(--shadow-card)' }}>
      {tabs.map((tab) => (
        <a
          key={tab.key}
          href={`/news?filter=${tab.key}`}
          style={{
            minHeight: 34,
            display: 'grid',
            placeItems: 'center',
            borderRadius: 11,
            fontSize: 11,
            fontWeight: 900,
            color: active === tab.key ? 'var(--primary)' : 'var(--muted)',
            background: active === tab.key ? 'var(--primary-soft)' : 'transparent',
          }}
        >
          {tab.label}
        </a>
      ))}
    </div>
  );
}
