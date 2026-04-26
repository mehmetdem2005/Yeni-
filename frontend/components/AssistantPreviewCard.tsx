import { Bot, Send } from 'lucide-react';

export function AssistantPreviewCard() {
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 className="card-title">Asistan</h2>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: 'var(--good)', fontSize: 11, fontWeight: 900 }}><span style={{ width: 7, height: 7, borderRadius: 99, background: 'var(--good)' }} /> Çevrimiçi</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '36px 1fr', gap: 10, alignItems: 'start' }}>
        <span className="icon-tile"><Bot size={19} /></span>
        <div style={{ background: 'var(--surface-soft)', borderRadius: 16, padding: 12, color: 'var(--text)', fontSize: 12, lineHeight: 1.45 }}>
          Piyasa genelinde temkinli iyimserlik hâkim. BTC güçlü destek üzerinde. Kısa vadede 69.200 direnci izlenmeli. Risk yönetimine dikkat etmeni öneririm.
        </div>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6 }}>
        {['Piyasa Özeti', 'Risk Analizi', 'Öneriler'].map((item) => (
          <a key={item} href="/assistant" style={{ minHeight: 34, display: 'grid', placeItems: 'center', borderRadius: 12, color: 'var(--primary)', background: 'var(--primary-soft)', fontSize: 11, fontWeight: 900 }}>{item}</a>
        ))}
      </div>
      <a href="/assistant" style={{ display: 'grid', gridTemplateColumns: '1fr 38px', gap: 8, alignItems: 'center' }}>
        <span style={{ minHeight: 42, display: 'flex', alignItems: 'center', padding: '0 12px', borderRadius: 14, border: '1px solid var(--border)', color: 'var(--muted)', fontSize: 12 }}>Bir soru sorun...</span>
        <span style={{ display: 'grid', placeItems: 'center', height: 42, borderRadius: 14, background: 'var(--primary)', color: '#fff' }}><Send size={16} /></span>
      </a>
    </section>
  );
}
