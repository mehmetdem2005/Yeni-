import { Activity, Bot, CandlestickChart, Newspaper, Settings } from 'lucide-react';

const items = [
  { href: '/', label: 'Ana', icon: Activity },
  { href: '/charts', label: 'Grafik', icon: CandlestickChart },
  { href: '/news', label: 'Haber', icon: Newspaper },
  { href: '/assistant', label: 'AI', icon: Bot },
  { href: '/settings', label: 'Ayar', icon: Settings },
];

export function MobileNav({ active }: { active: string }) {
  return (
    <nav className="mobile-bottom-nav">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <a key={item.href} className={active === item.href ? 'active' : ''} href={item.href}>
            <Icon size={16} /> {item.label}
          </a>
        );
      })}
    </nav>
  );
}
