import { CheckCircle2, Database, KeyRound, Server, ShieldAlert, ShieldCheck, Zap } from 'lucide-react';

type Runtime = {
  app_env?: string;
  min_api_interval_seconds?: number;
  groq_key_present?: boolean;
  supabase_url_present?: boolean;
  supabase_service_key_present?: boolean;
  database_url_present?: boolean;
};

type DatabaseInfo = {
  backend?: string;
  postgres_ready?: boolean;
  note?: string;
};

type SettingsRuntime = {
  runtime?: Runtime;
  database?: DatabaseInfo;
};

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, borderRadius: 999, padding: '6px 9px', background: ok ? 'var(--good-soft)' : 'var(--bad-soft)', color: ok ? 'var(--good)' : 'var(--bad)', fontSize: 11, fontWeight: 950 }}>
      {ok ? <CheckCircle2 size={14} /> : <ShieldAlert size={14} />}
      {label}
    </span>
  );
}

function SettingRow({ icon, title, desc, ok, okText, failText }: { icon: React.ReactNode; title: string; desc: string; ok: boolean; okText: string; failText: string }) {
  return (
    <article style={{ display: 'grid', gridTemplateColumns: '38px 1fr auto', gap: 10, alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
      <span className="icon-tile" style={{ color: ok ? 'var(--good)' : 'var(--bad)', background: ok ? 'var(--good-soft)' : 'var(--bad-soft)' }}>{icon}</span>
      <div>
        <b style={{ fontSize: 13 }}>{title}</b>
        <p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11, lineHeight: 1.35 }}>{desc}</p>
      </div>
      <StatusPill ok={ok} label={ok ? okText : failText} />
    </article>
  );
}

export function SettingsStatusCard({ data }: { data?: SettingsRuntime | null }) {
  const runtime = data?.runtime ?? {};
  const database = data?.database ?? {};
  const groqOk = Boolean(runtime.groq_key_present);
  const supabaseOk = Boolean(runtime.supabase_url_present && runtime.supabase_service_key_present);
  const databaseOk = Boolean(runtime.database_url_present || database.backend === 'postgres');
  const interval = runtime.min_api_interval_seconds ?? 10;

  return (
    <section className="card" style={{ display: 'grid', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div style={{ color: 'var(--muted)', fontSize: 11, fontWeight: 900 }}>SİSTEM BAĞLANTILARI</div>
          <h2 className="card-title" style={{ marginTop: 3 }}>Runtime Durumu</h2>
        </div>
        <span className="chip">{runtime.app_env || 'cloud'}</span>
      </div>

      <div>
        <SettingRow icon={<KeyRound size={18} />} title="Groq API" desc="AI asistan, 10 dakikalık yorum ve model yönlendirme için kullanılır." ok={groqOk} okText="Aktif" failText="Eksik" />
        <SettingRow icon={<Database size={18} />} title="Supabase" desc="Postgres veritabanı, haber, log, işlem ve grafik verilerini saklar." ok={supabaseOk} okText="Bağlı" failText="Eksik" />
        <SettingRow icon={<Server size={18} />} title="Database URL" desc={`Aktif backend: ${database.backend || 'bilinmiyor'}.`} ok={databaseOk} okText="Hazır" failText="Fallback" />
        <article style={{ display: 'grid', gridTemplateColumns: '38px 1fr auto', gap: 10, alignItems: 'center', padding: '10px 0' }}>
          <span className="icon-tile"><Zap size={18} /></span>
          <div>
            <b style={{ fontSize: 13 }}>Rate Limit Koruması</b>
            <p style={{ margin: '3px 0 0', color: 'var(--muted)', fontSize: 11 }}>API istekleri en az {interval} saniye aralıkla çalışır.</p>
          </div>
          <StatusPill ok={interval >= 10} label={`${interval}s`} />
        </article>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 10, alignItems: 'center', padding: 10, borderRadius: 15, background: 'var(--surface-soft)' }}>
        <span style={{ display: 'grid', placeItems: 'center', color: 'var(--good)' }}><ShieldCheck size={18} /></span>
        <p style={{ margin: 0, color: 'var(--muted)', fontSize: 12, lineHeight: 1.4 }}>
          API keyler frontend içinde gösterilmez. Secret değerleri Render/Supabase environment alanlarında tutulmalıdır.
        </p>
      </div>
    </section>
  );
}
