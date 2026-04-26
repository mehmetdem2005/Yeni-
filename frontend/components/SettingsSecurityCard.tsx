import { AlertTriangle, BadgeCheck, LockKeyhole, Power, ShieldCheck } from 'lucide-react';

export function SettingsSecurityCard() {
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 11, fontWeight: 900 }}>GÜVENLİK</div>
          <h2 className="card-title" style={{ marginTop: 3 }}>İşlem Güvenliği</h2>
        </div>
        <span className="icon-tile" style={{ color: 'var(--good)', background: 'var(--good-soft)' }}><ShieldCheck size={18} /></span>
      </div>

      <div style={{ display: 'grid', gap: 8 }}>
        <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr auto', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: 'var(--good-soft)' }}>
          <BadgeCheck size={18} color="var(--good)" />
          <div><b style={{ fontSize: 13 }}>Paper Trade Modu</b><p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11 }}>Gerçek para emri kapalı tutulmalıdır.</p></div>
          <b style={{ color: 'var(--good)', fontSize: 12 }}>Aktif</b>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr auto', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: 'var(--surface-soft)' }}>
          <LockKeyhole size={18} color="var(--primary)" />
          <div><b style={{ fontSize: 13 }}>Withdrawal Kapalı</b><p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11 }}>API anahtarlarında para çekme izni olmamalı.</p></div>
          <b style={{ color: 'var(--primary)', fontSize: 12 }}>Zorunlu</b>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr auto', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: 'var(--bad-soft)' }}>
          <Power size={18} color="var(--bad)" />
          <div><b style={{ fontSize: 13 }}>Acil Durdurma</b><p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11 }}>Tüm açık pozisyonları kapatacak anahtar planlanmıştır.</p></div>
          <b style={{ color: 'var(--bad)', fontSize: 12 }}>Manuel</b>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: 'var(--warning-soft)' }}>
        <AlertTriangle size={18} color="var(--warning)" />
        <p style={{ margin: 0, color: 'var(--muted)', fontSize: 12, lineHeight: 1.4 }}>
          Bu panel canlı para için hazır değildir. Test kriterleri tamamlanmadan gerçek emir açılmamalıdır.
        </p>
      </div>
    </section>
  );
}
