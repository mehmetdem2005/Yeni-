import { AlertTriangle, Bot, Database, LineChart, Settings, Shield, TrendingUp, Users } from 'lucide-react';

type LogRow = {
  created_at?: string;
  channel?: string;
  level?: string;
  message?: string;
  user_explanation?: string;
};

const channelMeta: Record<string, { label: string; color: string; bg: string; Icon: typeof Settings }> = {
  system: { label: 'Sistem', color: '#2563eb', bg: '#eaf1ff', Icon: Settings },
  trade: { label: 'İşlem', color: '#16a34a', bg: '#e8f8ef', Icon: TrendingUp },
  indicator: { label: 'İndikatör', color: '#7c3aed', bg: '#f1edff', Icon: LineChart },
  family: { label: 'Aile', color: '#f59e0b', bg: '#fff7e6', Icon: Users },
  data: { label: 'Veri', color: '#0f766e', bg: '#e6fffa', Icon: Database },
  ai: { label: 'AI', color: '#2563eb', bg: '#eaf1ff', Icon: Bot },
  risk: { label: 'Risk', color: '#f59e0b', bg: '#fff7e6', Icon: Shield },
  error: { label: 'Hata', color: '#dc2626', bg: '#feecec', Icon: AlertTriangle },
};

function formatTime(value?: string) {
  if (!value) return '10:42:11';
  try {
    return new Intl.DateTimeFormat('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(value));
  } catch {
    return value;
  }
}

const fallbackLogs: LogRow[] = [
  { channel: 'system', message: 'Sistem başarıyla başlatıldı.', created_at: '' },
  { channel: 'trade', message: 'BTC/USDT için AL sinyali üretildi.', created_at: '' },
  { channel: 'indicator', message: 'RSI 14 nötr bölgeye geçti.', created_at: '' },
  { channel: 'family', message: 'Veri toplama tamamlandı.', created_at: '' },
  { channel: 'error', message: 'SOL/USDT emir iptal edildi.', created_at: '' },
];

export function LiveLogCard({ logs }: { logs?: LogRow[] }) {
  const rows = logs?.length ? logs.slice(0, 5) : fallbackLogs;
  return (
    <section className="card" style={{ display: 'grid', gap: 4 }}>
      {rows.map((log, index) => {
        const meta = channelMeta[String(log.channel || 'system')] ?? channelMeta.system;
        const Icon = meta.Icon;
        return (
          <article key={`${log.created_at}-${index}`} style={{ display: 'grid', gridTemplateColumns: '40px 1fr auto', gap: 10, alignItems: 'center', padding: '10px 0', borderBottom: index === rows.length - 1 ? 0 : '1px solid var(--border)' }}>
            <span style={{ display: 'grid', placeItems: 'center', width: 34, height: 34, borderRadius: 12, color: meta.color, background: meta.bg }}>
              <Icon size={18} />
            </span>
            <div>
              <b style={{ color: meta.color, fontSize: 12 }}>{meta.label}</b>
              <p style={{ margin: '3px 0 0', color: 'var(--text)', fontSize: 12, lineHeight: 1.35 }}>{log.message}</p>
            </div>
            <small style={{ color: 'var(--muted-2)', fontSize: 10, whiteSpace: 'nowrap' }}>{formatTime(log.created_at)}</small>
          </article>
        );
      })}
      <a href="/logs?tab=logs" style={{ color: 'var(--primary)', fontSize: 12, fontWeight: 900, textAlign: 'center', paddingTop: 8 }}>Tüm Logları Gör ›</a>
    </section>
  );
}
