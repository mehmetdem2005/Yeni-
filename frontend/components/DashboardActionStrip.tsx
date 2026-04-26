'use client';

import { useEffect, useState } from 'react';
import { Database, GraduationCap, Loader2, Pause, Play, Power } from 'lucide-react';
import { apiGet, apiPost } from '@/lib/api';

type AutomationStatus = {
  running?: boolean;
  note?: string;
  cycle_count?: number;
  last_cycle_at?: string | null;
};

type ActionState = {
  running: boolean;
  message: string;
  busy: string | null;
  cycleCount?: number;
};

export function DashboardActionStrip() {
  const [state, setState] = useState<ActionState>({ running: false, message: 'Hazır', busy: null });

  useEffect(() => {
    apiGet<AutomationStatus>('/api/control/status')
      .then((data) => setState((prev) => ({ ...prev, running: Boolean(data.running), message: data.note || prev.message, cycleCount: data.cycle_count })))
      .catch(() => undefined);
  }, []);

  async function runAction(label: string, path: string, nextRunning?: boolean) {
    if (state.busy) return;
    setState((prev) => ({ ...prev, busy: label, message: `${label} çalışıyor...` }));
    try {
      const data = await apiPost<AutomationStatus | Record<string, unknown>>(path);
      const auto = data as AutomationStatus;
      setState((prev) => ({
        running: nextRunning ?? auto.running ?? prev.running,
        busy: null,
        message: auto.note || `${label} tamamlandı`,
        cycleCount: auto.cycle_count ?? prev.cycleCount,
      }));
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
        <button className="action-btn green" type="button" onClick={() => runAction('Başlat', '/api/control/start', true)}>
          {icon('Başlat', Play)}Başlat
        </button>
        <button className="action-btn red" type="button" onClick={() => runAction('Durdur', '/api/control/stop', false)}>
          {icon('Durdur', Pause)}Durdur
        </button>
        <button className="action-btn" type="button" onClick={() => runAction('Tek Tur', '/api/cycle')}>
          {icon('Tek Tur', Power)}Tek Tur
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
        <span style={{ color: state.running ? 'var(--good)' : 'var(--muted)' }}>
          {state.running ? `Çalışıyor${state.cycleCount !== undefined ? ` · ${state.cycleCount} tur` : ''}` : 'Beklemede'}
        </span>
      </div>
    </section>
  );
}
