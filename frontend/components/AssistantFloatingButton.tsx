import { Bot } from 'lucide-react';

export function AssistantFloatingButton() {
  return (
    <a
      href="/assistant"
      className="assistant-fab"
      aria-label="AI Asistanı aç"
      title="AI Asistan"
    >
      <Bot size={20} />
    </a>
  );
}
