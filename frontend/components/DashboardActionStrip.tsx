'use client';

import { useState } from 'react';
import { Database, GraduationCap, Loader2, Pause, Play, Power } from 'lucide-react';
import { apiPost } from '@/lib/api';

type ActionState = {
  running: boolean;
  message: string;
  busy: string | null;
};

export function DashboardActionStrip() {
  const [state, setState] = useState<ActionState>({ running: false, message: 'Hazır', busy: null });

  async function runAction(label: string, path: string, nextRunning?: boolean) {
    if (state.busy) return;
    setState((prev) => ({ ...prev, busy: label, message: `${label} çalışıyor...` }));
    try {
      await apiPost(path);
      setState({ running: nextRunning ?? state.running, busy: null, message: `${label} tamamlandı` });
    } catch {
      setState((prev) => ({ ...prev, busy: null, message: `${label} başarısız oldu` }));
    }
  }

  function icon(label: string, Icon: typeof Play) {
    return state.busy === label ? <Loader2 className="spin" /> : <Icon />;
  }

  return (
    <section className="card" style={{ display: 'grid', gap: 9 }} aria-label="Kontrol paneli">
      <div className="action-grid">
        <button className="action-btn green" type="button" onClick={() => runAction('Başlat', '/api/cycle', true)}>
          {icon('Başlat', Play)}Başlat
        </button>
        <button className="action-btn red" type="button" onClick={() => setState({ running: false, busy: null, message: 'Otomatik çalışma durduruldu' })}>
          <Pause />Durdur
        </button>
        <button className="action-btn" type="button" onClick={() => runAction('Otomatik', '/api/cycle', true)}>
          {icon('Otomatik', Power)}Otomatik
        </button>
        <button className="action-btn purple" type="button" onClick={() => runAction('Veri Topla', '/api/collect')}>
          {icon('Veri Topla', Database)}Veri Topla
        </button>
        <button className="action-btn orange" type="button" onClick={() => runAction('Eğit', '/api/train')}>
          {icon('Eğit', GraduationCap)}Eğit
        </button>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, color: 'var(--muted)', fontSize: 11, fontWeight: 850 }}>
        <span>{state.message}</span>
        <span style={{ color: state.running ? 'var(--good)' : 'var(--muted)' }}>{state.running ? 'Çalışıyor' : 'Beklemede'}</span>
      </div>
    </section>
  );
}
