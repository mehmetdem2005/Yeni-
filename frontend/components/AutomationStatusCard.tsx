'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Loader2, RefreshCcw, ShieldAlert, TimerReset } from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';

type AutomationStatus = {
  running?: boolean;
  interval_seconds?: number;
  last_cycle_at?: string | null;
  cycle_count?: number;
  last_error?: string | null;
  note?: string;
};

type StatusResponse = { automation?: AutomationStatus };

function formatTime(value?: string | null) {
  if (!value) return 'Henüz yok';
  try {
    return new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(value));
  } catch {
    return value;
  }
}

export function AutomationStatusCard() {
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState('Durum yükleniyor...');

  async function refresh() {
    try {
      const data = await apiGet<StatusResponse>('/api/status');
      setStatus(data.automation ?? null);
      setMessage(data.automation?.note || 'Durum alındı');
    } catch {
      setMessage('Durum alınamadı');
    }
  }

  async function postAction(label: string, path: string) {
    setBusy(label);
    setMessage(`${label} çalışıyor...`);
    try {
      await apiPost(path);
      await refresh();
      setMessage(`${label} tamamlandı`);
    } catch {
      setMessage(`${label} başarısız oldu`);
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => { refresh(); }, []);

  const running = Boolean(status?.running);
  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10 }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 11, fontWeight: 900 }}>OTOMASYON</div>
          <h2 className="card-title" style={{ marginTop: 3 }}>Canlı Kontrol Durumu</h2>
        </div>
        <button type="button" onClick={refresh} style={{ border: 0, width: 36, height: 36, borderRadius: 12, background: 'var(--surface-soft)', color: 'var(--primary)', display: 'grid', placeItems: 'center' }}>
          <RefreshCcw size={17} />
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
        <div style={{ borderRadius: 14, background: running ? 'var(--good-soft)' : 'var(--surface-soft)', padding: 9, textAlign: 'center' }}>
          <b style={{ color: running ? 'var(--good)' : 'var(--muted)' }}>{running ? 'Açık' : 'Kapalı'}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Durum</div>
        </div>
        <div style={{ borderRadius: 14, background: 'var(--surface-soft)', padding: 9, textAlign: 'center' }}>
          <b>{status?.cycle_count ?? 0}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Tur</div>
        </div>
        <div style={{ borderRadius: 14, background: 'var(--surface-soft)', padding: 9, textAlign: 'center' }}>
          <b>{status?.interval_seconds ?? 10}s</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Aralık</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: status?.last_error ? 'var(--bad-soft)' : 'var(--surface-soft)' }}>
        <TimerReset size={18} color={status?.last_error ? 'var(--bad)' : 'var(--primary)'} />
        <div>
          <b style={{ fontSize: 12 }}>Son cycle: {formatTime(status?.last_cycle_at)}</b>
          <p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11, lineHeight: 1.35 }}>{status?.last_error || message}</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <button type="button" onClick={() => postAction('Acil Kapat', '/api/emergency/close-all')} style={{ minHeight: 46, border: 0, borderRadius: 14, background: 'var(--bad)', color: '#fff', fontWeight: 950, display: 'inline-flex', justifyContent: 'center', alignItems: 'center', gap: 7 }}>
          {busy === 'Acil Kapat' ? <Loader2 className="spin" size={17} /> : <ShieldAlert size={17} />} Acil Kapat
        </button>
        <button type="button" onClick={() => postAction('Hesabı Sıfırla', '/api/reset-paper-account')} style={{ minHeight: 46, border: '1px solid var(--border)', borderRadius: 14, background: '#fff', color: 'var(--bad)', fontWeight: 950, display: 'inline-flex', justifyContent: 'center', alignItems: 'center', gap: 7 }}>
          {busy === 'Hesabı Sıfırla' ? <Loader2 className="spin" size={17} /> : <AlertTriangle size={17} />} Sıfırla
        </button>
      </div>
    </section>
  );
}
