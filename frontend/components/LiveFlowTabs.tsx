type Props = {
  active: 'logs' | 'news' | 'assistant';
};

const tabs = [
  { key: 'logs', label: 'Canlı Loglar', href: '/logs?tab=logs' },
  { key: 'news', label: 'Haberler', href: '/logs?tab=news' },
  { key: 'assistant', label: 'Asistan', href: '/logs?tab=assistant' },
] as const;

export function LiveFlowTabs({ active }: Props) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', padding: 3, borderRadius: 14, border: '1px solid var(--border)', background: '#fff', boxShadow: 'var(--shadow-card)' }}>
      {tabs.map((tab) => (
        <a
          key={tab.key}
          href={tab.href}
          style={{
            minHeight: 36,
            display: 'grid',
            placeItems: 'center',
            borderRadius: 11,
            fontSize: 12,
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
