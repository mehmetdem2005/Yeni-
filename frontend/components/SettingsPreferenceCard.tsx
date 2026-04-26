import { BarChart3, Bell, Bot, CandlestickChart, Moon, SlidersHorizontal } from 'lucide-react';

function ToggleRow({ icon, title, desc, checked = true }: { icon: React.ReactNode; title: string; desc: string; checked?: boolean }) {
  return (
    <article style={{ display: 'grid', gridTemplateColumns: '38px 1fr auto', gap: 10, alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <span className="icon-tile">{icon}</span>
      <div>
        <b style={{ fontSize: 13 }}>{title}</b>
        <p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11, lineHeight: 1.35 }}>{desc}</p>
      </div>
      <input type="checkbox" defaultChecked={checked} style={{ width: 18, height: 18, accentColor: 'var(--primary)' }} />
    </article>
  );
}

export function SettingsPreferenceCard() {
  return (
    <section className="card" style={{ display: 'grid', gap: 8 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 11, fontWeight: 900 }}>KULLANICI TERCİHLERİ</div>
          <h2 className="card-title" style={{ marginTop: 3 }}>Panel Ayarları</h2>
        </div>
        <span className="icon-tile"><SlidersHorizontal size={18} /></span>
      </div>

      <div>
        <ToggleRow icon={<CandlestickChart size={18} />} title="Mum grafikleri" desc="Ana grafik ekranında mum görünümü varsayılan açık olur." />
        <ToggleRow icon={<BarChart3 size={18} />} title="İndikatör panelleri" desc="RSI, MACD, ATR, ADX ve MFI panelleri gösterilir." />
        <ToggleRow icon={<Bot size={18} />} title="AI ana yorum" desc="Ana sayfada 10 dakikalık özet yorum kartı görünür." />
        <ToggleRow icon={<Bell size={18} />} title="Haber ve balina işaretleri" desc="Grafikte haber ve balina markerları gösterilir." />
        <ToggleRow icon={<Moon size={18} />} title="Koyu mod" desc="Şimdilik kapalı. Beyaz arayüz ana tasarım hedefidir." checked={false} />
      </div>
    </section>
  );
}
