import { Database, GraduationCap, Pause, Play, Power } from 'lucide-react';

export function DashboardActionStrip() {
  return (
    <section className="card action-grid" aria-label="Kontrol butonları">
      <button className="action-btn green" type="button"><Play />Başlat</button>
      <button className="action-btn red" type="button"><Pause />Durdur</button>
      <button className="action-btn" type="button"><Power />Otomatik</button>
      <button className="action-btn purple" type="button"><Database />Veri Topla</button>
      <button className="action-btn orange" type="button"><GraduationCap />Eğit</button>
    </section>
  );
}
