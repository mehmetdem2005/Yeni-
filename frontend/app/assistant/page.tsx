import { Bot } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';

export default function AssistantPage() {
  return (
    <main className="app-shell">
      <section className="card" style={{ display: 'grid', gap: 12 }}>
        <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>AI ASİSTAN</div>
        <h1 style={{ margin: 0, fontSize: 22 }}>Sisteme Sor</h1>
        <p style={{ color: 'var(--muted)', lineHeight: 1.55, margin: 0 }}>
          Burada Groq destekli asistan panel verilerini okuyup sana sade şekilde açıklayacak. Emir açmayacak, sadece sistemi anlatacak.
        </p>
        <div style={{ background: 'var(--surface-soft)', borderRadius: 18, padding: 14 }}>
          <Bot color="var(--primary)" />
          <p style={{ fontWeight: 800 }}>Örnek sorular:</p>
          <ul style={{ margin: 0, paddingLeft: 20, color: 'var(--muted)' }}>
            <li>Neden işlem açmadı?</li>
            <li>BTC şu an ne anlatıyor?</li>
            <li>Risk neden yüksek?</li>
            <li>Haberler kararı etkiliyor mu?</li>
          </ul>
        </div>
      </section>
      <MobileNav active="/assistant" />
    </main>
  );
}
