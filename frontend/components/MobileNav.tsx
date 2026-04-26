import { BarChart3, BriefcaseBusiness, Home, Newspaper, ScrollText, Settings } from 'lucide-react';

const items = [
  { href: '/', label: 'Ana Sayfa', icon: Home },
  { href: '/charts', label: 'Grafikler', icon: BarChart3 },
  { href: '/portfolio', label: 'Portföy', icon: BriefcaseBusiness },
  { href: '/logs', label: 'Loglar', icon: ScrollText },
  { href: '/news', label: 'Haberler', icon: Newspaper },
  { href: '/settings', label: 'Ayarlar', icon: Settings },
];

export function MobileNav({ active }: { active: string }) {
  return (
    <nav className="mobile-bottom-nav">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <a key={item.href} className={active === item.href ? 'active' : ''} href={item.href}>
            <Icon />
            <span>{item.label}</span>
          </a>
        );
      })}
    </nav>
  );
}
