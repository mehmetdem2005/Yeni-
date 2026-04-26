import { Bot, ChevronRight } from 'lucide-react';

export function AiSummaryCard({ text }: { text?: string }) {
  return (
    <section className="card" style={{ display: 'grid', gridTemplateColumns: '38px 1fr 20px', gap: 10, alignItems: 'start' }}>
      <span className="icon-tile"><Bot size={19} /></span>
      <div>
        <h2 className="card-title">Yapay Zekâ Yorumu</h2>
        <p className="card-muted" style={{ margin: '8px 0 12px' }}>
          {text || 'Piyasa nötr-pozitif bölgede. Bitcoin güçlü desteğin üzerinde tutunuyor. Hacim artışı devam ediyor, kısa vadede yukarı yönlü kırılım olasılığı yüksek.'}
        </p>
        <a href="/assistant" style={{ color: 'var(--primary)', fontWeight: 900, fontSize: 12 }}>Detaylı Analiz</a>
      </div>
      <ChevronRight size={18} color="var(--primary)" style={{ alignSelf: 'center' }} />
    </section>
  );
}
