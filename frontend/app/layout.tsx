import type { Metadata, Viewport } from 'next';
import { AssistantFloatingButton } from '@/components/AssistantFloatingButton';
import './globals.css';

export const metadata: Metadata = {
  title: 'Kripto AI Kontrol Merkezi',
  description: 'Paper-trade, AI yorum, grafik, haber ve balina takip paneli.',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#f6f8fc',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>
        {children}
        <AssistantFloatingButton />
      </body>
    </html>
  );
}
