import { MoreVertical, RefreshCcw } from 'lucide-react';
import { MobileNav } from '@/components/MobileNav';
import { SettingsPreferenceCard } from '@/components/SettingsPreferenceCard';
import { SettingsSecurityCard } from '@/components/SettingsSecurityCard';
import { SettingsStatusCard } from '@/components/SettingsStatusCard';
import { apiGet } from '@/lib/api';

type SettingsRuntime = {
  runtime?: {
    app_env?: string;
    min_api_interval_seconds?: number;
    groq_key_present?: boolean;
    supabase_url_present?: boolean;
    supabase_service_key_present?: boolean;
    database_url_present?: boolean;
  };
  database?: {
    backend?: string;
    postgres_ready?: boolean;
    note?: string;
  };
};

async function getRuntime(): Promise<SettingsRuntime | null> {
  try {
    return await apiGet<SettingsRuntime>('/api/settings/runtime');
  } catch {
    return null;
  }
}

export default async function SettingsPage() {
  const runtime = await getRuntime();

  return (
    <main className="app-shell">
      <header className="page-title-row">
        <h1 className="page-title">Ayarlar</h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <a href="/settings" style={{ color: 'var(--primary)', display: 'grid', placeItems: 'center' }}><RefreshCcw size={20} /></a>
          <MoreVertical size={22} color="var(--text)" />
        </div>
      </header>

      <div style={{ display: 'grid', gap: 10 }}>
        <SettingsStatusCard data={runtime} />
        <SettingsPreferenceCard />
        <SettingsSecurityCard />
      </div>

      <MobileNav active="/settings" />
    </main>
  );
}
