import { Activity, Bot, CandlestickChart, Newspaper, Settings } from 'lucide-react';
import { apiGet } from '@/lib/api';

type StatusResponse = {
  db_rows?: number;
  trade_stats?: { closed_count?: number; open_count?: number; win_rate?: number; total_pnl?: number };
  wallet?: { cash?: number; starting_balance?: number };
  system_confidence?: { system_confidence?: number; status?: string; explanation?: string };
  database?: { backend?: string; note?: string };
};

function pct(value?: number) {
  if (value === undefined || value === null) return '—';
  return `%${(value * 100).toFixed(1)}`;
}

function money(value?: number) {
  if (value === undefined || value === null) return '—';
  return `${value.toLocaleString('tr-TR', { maximumFractionDigits: 2 })} USDT`;
}

async function getStatus(): Promise<StatusResponse | null> {
  try {
    return await apiGet<StatusResponse>('/api/status');
  } catch {
    return null;
  }
}

export default async function HomePage() {
  const status = await getStatus();
  const confidence = status?.system_confidence?.system_confidence ?? 0;
  const closed = status?.trade_stats?.closed_count ?? 0;
  const proof = Math.min(closed / 100, 1);

  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
          <div>
            <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>AI CANLI YORUM</div>
            <h1 style={{ margin: '4px 0 0', fontSize: 22 }}>Kripto AI Kontrol Merkezi</h1>
          </div>
          <Bot size={28} color="var(--primary)" />
        </div>
        <p style={{ margin: 0, color: 'var(--muted)', lineHeight: 1.55 }}>
          Kral, bu ekran V3 framework tabanlı yeni panelin başlangıcı. Sistem artık FastAPI backend + Next.js/Vercel frontend mimarisine geçiyor. Burada grafikler, haberler, balina akışı ve AI asistan modüler şekilde büyüyecek.
        </p>
      </section>

      <section className="compact-grid" style={{ marginTop: 12 }}>
        <div className="card">
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>Sistem Özgüveni</div>
          <div style={{ fontSize: 24, fontWeight: 900 }}>{pct(confidence)}</div>
          <small>{closed === 0 ? 'Henüz ölçülmedi' : `${closed} kapanmış işlem`}</small>
        </div>
        <div className="card">
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>Kanıt Gücü</div>
          <div style={{ fontSize: 24, fontWeight: 900 }}>{pct(proof)}</div>
          <small>İşlem sayısına göre güvenilirlik</small>
        </div>
        <div className="card">
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>Sanal Nakit</div>
          <div style={{ fontSize: 18, fontWeight: 900 }}>{money(status?.wallet?.cash)}</div>
          <small>Paper trade cüzdanı</small>
        </div>
        <div className="card">
          <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>Veri Satırı</div>
          <div style={{ fontSize: 24, fontWeight: 900 }}>{status?.db_rows ?? '—'}</div>
          <small>{status?.database?.backend ?? 'backend yok'}</small>
        </div>
      </section>

      <section className="card" style={{ marginTop: 12 }}>
        <h2 style={{ margin: '0 0 10px', fontSize: 18 }}>Sıradaki Framework Modülleri</h2>
        <div style={{ display: 'grid', gap: 8 }}>
          {[
            'TradingView Lightweight Charts ile mum grafikleri',
            'AI Asistan sohbet ekranı',
            'Haber + etki skoru paneli',
            'Balina / emir akışı paneli',
            'Ayarlar ve API key yönetimi',
          ].map((item) => (
            <div key={item} style={{ padding: 12, background: 'var(--surface-soft)', borderRadius: 16, fontWeight: 700 }}>
              {item}
            </div>
          ))}
        </div>
      </section>

      <nav className="mobile-bottom-nav">
        <a className="active" href="#"><Activity size={16} /> Ana</a>
        <a href="#"><CandlestickChart size={16} /> Grafik</a>
        <a href="#"><Newspaper size={16} /> Haber</a>
        <a href="#"><Bot size={16} /> AI</a>
        <a href="#"><Settings size={16} /> Ayar</a>
      </nav>
    </main>
  );
}
