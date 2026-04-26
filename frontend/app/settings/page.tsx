import { KeyRound, Settings } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';

export default function SettingsPage() {
  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 12 }}>
        <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>AYARLAR</div>
        <h1 style={{ margin: 0, fontSize: 22 }}>API Key ve Sistem Ayarları</h1>
        <p style={{ color: 'var(--muted)', lineHeight: 1.55, margin: 0 }}>
          API keyler frontend içinde açık saklanmayacak. Ayarlar güvenli backend endpointleri üzerinden yönetilecek.
        </p>
        <div className="compact-grid">
          <div className="card" style={{ boxShadow: 'none' }}><KeyRound color="var(--primary)" /><b>Groq API</b><small>AI asistan ve 10 dk yorum</small></div>
          <div className="card" style={{ boxShadow: 'none' }}><KeyRound color="var(--primary)" /><b>Supabase</b><small>Postgres veri tabanı</small></div>
          <div className="card" style={{ boxShadow: 'none' }}><KeyRound color="var(--primary)" /><b>Binance</b><small>Public data, paper-trade</small></div>
          <div className="card" style={{ boxShadow: 'none' }}><Settings color="var(--primary)" /><b>Grafik</b><small>Renk, boy, indikatör</small></div>
        </div>
      </section>
      <MobileNav active="/settings" />
    </main>
  );
}
