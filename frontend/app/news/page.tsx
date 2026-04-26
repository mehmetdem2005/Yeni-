import { Newspaper } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';

export default function NewsPage() {
  return (
    <main className="app-shell">
      <section className="card">
        <div style={{ color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>HABER AKIŞI</div>
        <h1 style={{ margin: '4px 0 8px', fontSize: 22 }}>Haber + Etki Skoru</h1>
        <p style={{ color: 'var(--muted)', lineHeight: 1.55 }}>
          Haberler karar ağırlığına katılacak ama tek başına işlem açtırmayacak. Pozitif haber destek, negatif haber risk azaltıcı olarak çalışacak.
        </p>
        <div style={{ display: 'grid', placeItems: 'center', minHeight: 220, background: 'var(--surface-soft)', borderRadius: 18 }}>
          <Newspaper size={44} color="var(--primary)" />
        </div>
      </section>
      <MobileNav active="/news" />
    </main>
  );
}
