type MarkerKind = 'trade' | 'news' | 'whale';

type Marker = {
  kind?: MarkerKind;
  time: string;
  text: string;
  color: string;
  title?: string;
  sentiment?: string;
  impact_score?: number;
  event_type?: string;
  score?: number;
  notional?: number;
  price?: number;
};

type Props = {
  markers: Marker[];
};

function kindLabel(kind?: string) {
  if (kind === 'news') return 'Haber';
  if (kind === 'whale') return 'Balina';
  return 'İşlem';
}

function formatTime(value: string) {
  try {
    return new Intl.DateTimeFormat('tr-TR', {
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function money(value?: number) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return null;
  return `${Number(value).toLocaleString('tr-TR', { maximumFractionDigits: 0 })} USDT`;
}

function score(value?: number) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) return null;
  return Number(value).toFixed(2);
}

function detail(marker: Marker) {
  if (marker.kind === 'news') {
    return marker.title || `Duygu: ${marker.sentiment ?? 'nötr'} · Etki: ${score(marker.impact_score) ?? '—'}`;
  }
  if (marker.kind === 'whale') {
    const parts = [marker.event_type, money(marker.notional), marker.price ? `Fiyat: ${marker.price}` : null, marker.score ? `Skor: ${score(marker.score)}` : null].filter(Boolean);
    return parts.join(' · ') || 'Balina / emir akışı olayı';
  }
  return marker.price ? `Fiyat: ${marker.price}` : marker.text;
}

export function ChartMarkerLegend({ markers }: Props) {
  if (!markers.length) return null;
  const recent = [...markers]
    .sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime())
    .slice(0, 12);

  return (
    <section className="card" style={{ boxShadow: 'none', display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 900 }}>GRAFİK İŞARETLERİ</div>
          <h2 style={{ margin: 0, fontSize: 17 }}>Son Marker Detayları</h2>
        </div>
        <small style={{ color: 'var(--muted)', fontWeight: 800 }}>{recent.length}/{markers.length}</small>
      </div>
      <div style={{ display: 'grid', gap: 8 }}>
        {recent.map((marker, index) => (
          <article key={`${marker.time}-${marker.text}-${index}`} style={{ display: 'grid', gridTemplateColumns: '10px 1fr', gap: 10, alignItems: 'start', padding: 10, borderRadius: 15, background: 'var(--surface-soft)' }}>
            <span style={{ width: 10, height: 10, marginTop: 5, borderRadius: 999, background: marker.color }} />
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8, alignItems: 'center' }}>
                <b>{kindLabel(marker.kind)} · {marker.text}</b>
                <small style={{ color: 'var(--muted)', whiteSpace: 'nowrap' }}>{formatTime(marker.time)}</small>
              </div>
              <p style={{ margin: '4px 0 0', color: 'var(--muted)', lineHeight: 1.45 }}>{detail(marker)}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
