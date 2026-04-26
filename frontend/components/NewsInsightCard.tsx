import { Bot, RefreshCcw } from 'lucide-react';

export function NewsInsightCard() {
  return (
    <section className="card" style={{ display: 'grid', gridTemplateColumns: '38px 1fr auto', gap: 10, alignItems: 'start' }}>
      <span className="icon-tile"><Bot size={19} /></span>
      <div>
        <h2 className="card-title">Haber Yorumu</h2>
        <p className="card-muted" style={{ margin: '7px 0 0' }}>
          Haber akışı şu an piyasayı tek başına çevirecek kadar güçlü değil. Pozitif ETF girişleri destekleyici, fakat makro veriler risk iştahını sınırlıyor. Sistem haberleri yardımcı ağırlık olarak kullanır; tek başına işlem açmaz.
        </p>
      </div>
      <a href="/logs?tab=news" title="Yenile" style={{ width: 34, height: 34, display: 'grid', placeItems: 'center', borderRadius: 12, background: 'var(--surface-soft)', color: 'var(--primary)' }}>
        <RefreshCcw size={17} />
      </a>
    </section>
  );
}
