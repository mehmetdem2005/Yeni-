'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, Loader2, RefreshCcw, ServerCog, ShieldAlert, TimerReset, X } from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';

type AutomationStatus = {
  running?: boolean;
  interval_seconds?: number;
  last_cycle_at?: string | null;
  cycle_count?: number;
  last_error?: string | null;
  note?: string;
};

type WorkerStatus = {
  status?: string;
  running?: boolean;
  cycle_count?: number;
  interval_seconds?: number;
  last_error?: string | null;
  heartbeat_at?: string;
  updated_at?: string;
};

type StatusResponse = { automation?: AutomationStatus; worker?: WorkerStatus | null };

type ConfirmAction = {
  label: string;
  path: string;
  title: string;
  body: string;
  dangerText: string;
} | null;

const intervals = [10, 30, 60, 300];

function formatTime(value?: string | null) {
  if (!value) return 'Henüz yok';
  try {
    return new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(value));
  } catch {
    return value;
  }
}

function intervalLabel(value: number) {
  if (value < 60) return `${value}s`;
  if (value === 60) return '1dk';
  return `${Math.round(value / 60)}dk`;
}

function heartbeatFresh(value?: string | null, intervalSeconds = 300) {
  if (!value) return false;
  const ageMs = Date.now() - new Date(value).getTime();
  if (!Number.isFinite(ageMs)) return false;
  return ageMs < Math.max(intervalSeconds * 3, 120) * 1000;
}

export function AutomationStatusCard() {
  const [status, setStatus] = useState<AutomationStatus | null>(null);
  const [worker, setWorker] = useState<WorkerStatus | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState('Durum yükleniyor...');
  const [confirmAction, setConfirmAction] = useState<ConfirmAction>(null);

  async function refresh() {
    try {
      const data = await apiGet<StatusResponse>('/api/status');
      setStatus(data.automation ?? null);
      setWorker(data.worker ?? null);
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
      setConfirmAction(null);
    }
  }

  async function updateInterval(seconds: number) {
    setBusy(`interval-${seconds}`);
    setMessage(`${intervalLabel(seconds)} aralığı ayarlanıyor...`);
    try {
      const data = await apiPost<AutomationStatus>('/api/control/interval', { interval_seconds: seconds });
      setStatus(data);
      setMessage(data.note || `Aralık ${intervalLabel(seconds)} yapıldı`);
    } catch {
      setMessage('Aralık güncellenemedi');
    } finally {
      setBusy(null);
    }
  }

  useEffect(() => { refresh(); }, []);

  const running = Boolean(status?.running);
  const activeInterval = status?.interval_seconds ?? 10;
  const workerBeat = worker?.heartbeat_at ?? worker?.updated_at;
  const workerAlive = heartbeatFresh(workerBeat, worker?.interval_seconds ?? 300);
  return (
    <section className="card" style={{ display: 'grid', gap: 10, position: 'relative' }}>
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
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Panel</div>
        </div>
        <div style={{ borderRadius: 14, background: 'var(--surface-soft)', padding: 9, textAlign: 'center' }}>
          <b>{status?.cycle_count ?? 0}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Panel Tur</div>
        </div>
        <div style={{ borderRadius: 14, background: 'var(--surface-soft)', padding: 9, textAlign: 'center' }}>
          <b>{intervalLabel(activeInterval)}</b>
          <div style={{ color: 'var(--muted)', fontSize: 10, fontWeight: 800 }}>Panel Aralık</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: workerAlive ? 'var(--good-soft)' : 'var(--surface-soft)' }}>
        <ServerCog size={18} color={workerAlive ? 'var(--good)' : 'var(--primary)'} />
        <div>
          <b style={{ fontSize: 12 }}>Worker: {workerAlive ? 'Canlı' : 'Bekliyor'} · {worker?.cycle_count ?? 0} tur</b>
          <p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11, lineHeight: 1.35 }}>
            Son heartbeat: {formatTime(workerBeat)}{worker?.last_error ? ` · Hata: ${worker.last_error}` : ''}
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: status?.last_error ? 'var(--bad-soft)' : 'var(--surface-soft)' }}>
        <TimerReset size={18} color={status?.last_error ? 'var(--bad)' : 'var(--primary)'} />
        <div>
          <b style={{ fontSize: 12 }}>Son panel cycle: {formatTime(status?.last_cycle_at)}</b>
          <p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11, lineHeight: 1.35 }}>{status?.last_error || message}</p>
        </div>
      </div>

      <div style={{ display: 'grid', gap: 7 }}>
        <div style={{ color: 'var(--muted)', fontSize: 11, fontWeight: 900 }}>PANEL ÇALIŞMA ARALIĞI</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 7 }}>
          {intervals.map((seconds) => {
            const active = activeInterval === seconds;
            const loading = busy === `interval-${seconds}`;
            return (
              <button
                key={seconds}
                type="button"
                onClick={() => updateInterval(seconds)}
                disabled={Boolean(busy)}
                style={{
                  minHeight: 38,
                  border: `1px solid ${active ? 'var(--primary)' : 'var(--border)'}`,
                  borderRadius: 13,
                  background: active ? 'var(--primary-soft)' : '#fff',
                  color: active ? 'var(--primary)' : 'var(--text)',
                  fontWeight: 950,
                  fontSize: 12,
                  display: 'grid',
                  placeItems: 'center',
                }}
              >
                {loading ? <Loader2 className="spin" size={15} /> : intervalLabel(seconds)}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <button type="button" onClick={() => setConfirmAction({ label: 'Acil Kapat', path: '/api/emergency/close-all', title: 'Açık pozisyonlar acil kapatılsın mı?', body: 'Bu işlem otomasyonu durdurur ve tüm açık paper-trade pozisyonlarını güncel bid fiyatıyla kapatmayı dener. Geri alınamaz.', dangerText: 'Evet, Acil Kapat' })} style={{ minHeight: 46, border: 0, borderRadius: 14, background: 'var(--bad)', color: '#fff', fontWeight: 950, display: 'inline-flex', justifyContent: 'center', alignItems: 'center', gap: 7 }}>
          {busy === 'Acil Kapat' ? <Loader2 className="spin" size={17} /> : <ShieldAlert size={17} />} Acil Kapat
        </button>
        <button type="button" onClick={() => setConfirmAction({ label: 'Hesabı Sıfırla', path: '/api/reset-paper-account', title: 'Paper hesabı sıfırlansın mı?', body: 'Bu işlem sanal hesap, paper pozisyonlar, equity geçmişi ve sinyal kayıtlarını sıfırlayabilir. Test geçmişini kaybetmek istemiyorsan basma.', dangerText: 'Evet, Sıfırla' })} style={{ minHeight: 46, border: '1px solid var(--border)', borderRadius: 14, background: '#fff', color: 'var(--bad)', fontWeight: 950, display: 'inline-flex', justifyContent: 'center', alignItems: 'center', gap: 7 }}>
          {busy === 'Hesabı Sıfırla' ? <Loader2 className="spin" size={17} /> : <AlertTriangle size={17} />} Sıfırla
        </button>
      </div>

      {confirmAction ? (
        <div style={{ position: 'fixed', inset: 0, zIndex: 60, display: 'grid', placeItems: 'center', background: 'rgba(15, 23, 42, 0.35)', padding: 18 }}>
          <div style={{ width: 'min(390px, 100%)', background: '#fff', borderRadius: 22, border: '1px solid var(--border)', boxShadow: '0 24px 80px rgba(15, 23, 42, 0.24)', padding: 14, display: 'grid', gap: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', gap: 10 }}>
              <div style={{ display: 'flex', gap: 10, alignItems: 'start' }}>
                <span style={{ display: 'grid', placeItems: 'center', width: 38, height: 38, borderRadius: 14, background: 'var(--bad-soft)', color: 'var(--bad)' }}><AlertTriangle size={20} /></span>
                <div>
                  <h3 style={{ margin: 0, fontSize: 16 }}>{confirmAction.title}</h3>
                  <p style={{ margin: '6px 0 0', color: 'var(--muted)', fontSize: 12, lineHeight: 1.45 }}>{confirmAction.body}</p>
                </div>
              </div>
              <button type="button" onClick={() => setConfirmAction(null)} style={{ border: 0, background: 'transparent', color: 'var(--muted)', padding: 4 }}><X size={19} /></button>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
              <button type="button" onClick={() => setConfirmAction(null)} style={{ minHeight: 44, border: '1px solid var(--border)', borderRadius: 14, background: '#fff', fontWeight: 950 }}>Vazgeç</button>
              <button type="button" onClick={() => postAction(confirmAction.label, confirmAction.path)} style={{ minHeight: 44, border: 0, borderRadius: 14, background: 'var(--bad)', color: '#fff', fontWeight: 950 }}>
                {busy === confirmAction.label ? 'Çalışıyor...' : confirmAction.dangerText}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
