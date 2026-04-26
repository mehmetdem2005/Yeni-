import { CandlestickChart, MoreVertical } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';

export default function ChartsPage() {
  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>GRAFİKLER</div>
            <h1 style={{ margin: 0, fontSize: 22 }}>Mum Grafikleri</h1>
          </div>
          <button aria-label="Grafik ayarları" style={{ border: 0, background: 'var(--surface-soft)', borderRadius: 14, padding: 10 }}>
            <MoreVertical size={20} />
          </button>
        </div>
        <div style={{ minHeight: 320, borderRadius: 18, background: 'linear-gradient(135deg, #ffffff, #eef3fb)', border: '1px solid var(--border)', display: 'grid', placeItems: 'center', color: 'var(--muted)', textAlign: 'center', padding: 20 }}>
          <div>
            <CandlestickChart size={42} color="var(--primary)" />
            <p style={{ fontWeight: 800 }}>TradingView Lightweight Charts burada bağlanacak.</p>
            <p style={{ margin: 0 }}>Mum, EMA, RSI, ATR, hacim, SL/TP ve haber/balina işaretleri bu ekranda olacak.</p>
          </div>
        </div>
      </section>
      <MobileNav active="/charts" />
    </main>
  );
}
