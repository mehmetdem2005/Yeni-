'use client';

import { useMemo, useState } from 'react';
import { Bot, Loader2, Send, Sparkles, UserRound } from 'lucide-react';
import { apiPost } from '@/lib/api';

type Message = {
  role: 'assistant' | 'user';
  content: string;
};

type AssistantResponse = {
  text?: string;
  content?: string;
  answer?: string;
  model?: string;
  provider?: string;
  fallback_used?: boolean;
};

const quickQuestions = [
  'Neden işlem açmadı?',
  'BTC şu an ne anlatıyor?',
  'Risk neden yüksek?',
  'Haberler kararı etkiliyor mu?',
  'Sistem özgüveni neye göre hesaplandı?',
  'Bugün neye dikkat etmeliyim?',
];

function responseText(data: AssistantResponse) {
  return data.text || data.content || data.answer || 'Asistan yanıt verdi ama metin alanı boş döndü.';
}

export function AssistantChatClient() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Kral, ben bu panelin asistanıyım. Grafikleri, haberleri, logları, paper-trade sonuçlarını ve risk durumunu sade şekilde açıklamak için buradayım. Emir açmam; sadece sistemi anlamana yardım ederim.',
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastModel, setLastModel] = useState<string | null>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !loading, [input, loading]);

  async function ask(question: string) {
    const clean = question.trim();
    if (!clean || loading) return;
    setInput('');
    setLoading(true);
    setMessages((prev) => [...prev, { role: 'user', content: clean }]);

    try {
      const data = await apiPost<AssistantResponse>('/api/assistant/ask', { question: clean });
      setLastModel(data.model ? `${data.provider ?? 'AI'} · ${data.model}` : null);
      setMessages((prev) => [...prev, { role: 'assistant', content: responseText(data) }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'Şu an asistan API bağlantısından yanıt alamadım. Groq API key, Render API ve /api/assistant/ask endpointini Ayarlar ekranından kontrol etmelisin.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="card" style={{ display: 'grid', gap: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span className="icon-tile"><Bot size={19} /></span>
          <div>
            <h2 className="card-title">Sisteme Sor</h2>
            <p className="card-muted" style={{ margin: '3px 0 0' }}>Groq destekli panel asistanı</p>
          </div>
        </div>
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: 'var(--good)', fontSize: 11, fontWeight: 950 }}>
          <span style={{ width: 7, height: 7, borderRadius: 99, background: 'var(--good)' }} /> Hazır
        </span>
      </div>

      <div style={{ display: 'flex', gap: 7, overflowX: 'auto', paddingBottom: 2 }}>
        {quickQuestions.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => ask(question)}
            style={{
              border: '1px solid var(--border)',
              background: '#fff',
              color: 'var(--primary)',
              borderRadius: 999,
              padding: '8px 10px',
              whiteSpace: 'nowrap',
              fontSize: 11,
              fontWeight: 900,
              boxShadow: 'var(--shadow-card)',
            }}
          >
            {question}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gap: 9, maxHeight: 430, overflowY: 'auto', padding: '2px 0' }}>
        {messages.map((message, index) => {
          const isUser = message.role === 'user';
          return (
            <article key={`${message.role}-${index}`} style={{ display: 'grid', gridTemplateColumns: isUser ? '1fr 34px' : '34px 1fr', gap: 9, alignItems: 'end' }}>
              {!isUser ? <span className="icon-tile"><Bot size={17} /></span> : null}
              <div
                style={{
                  justifySelf: isUser ? 'end' : 'start',
                  maxWidth: '100%',
                  background: isUser ? 'var(--primary)' : 'var(--surface-soft)',
                  color: isUser ? '#fff' : 'var(--text)',
                  borderRadius: isUser ? '17px 17px 4px 17px' : '17px 17px 17px 4px',
                  padding: 12,
                  fontSize: 12,
                  lineHeight: 1.48,
                  fontWeight: isUser ? 800 : 600,
                }}
              >
                {message.content}
              </div>
              {isUser ? <span className="icon-tile" style={{ color: '#fff', background: 'var(--primary)' }}><UserRound size={17} /></span> : null}
            </article>
          );
        })}
        {loading ? (
          <article style={{ display: 'grid', gridTemplateColumns: '34px 1fr', gap: 9, alignItems: 'center' }}>
            <span className="icon-tile"><Bot size={17} /></span>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, width: 'fit-content', background: 'var(--surface-soft)', borderRadius: 17, padding: 12, color: 'var(--muted)', fontSize: 12, fontWeight: 800 }}>
              <Loader2 size={16} className="spin" /> Verileri okuyorum...
            </div>
          </article>
        ) : null}
      </div>

      {lastModel ? (
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, color: 'var(--muted)', fontSize: 11, fontWeight: 800 }}>
          <Sparkles size={14} color="var(--primary)" /> Son model: {lastModel}
        </div>
      ) : null}

      <form
        onSubmit={(event) => {
          event.preventDefault();
          ask(input);
        }}
        style={{ display: 'grid', gridTemplateColumns: '1fr 44px', gap: 8, alignItems: 'center' }}
      >
        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Sisteme bir soru sor..."
          style={{
            minHeight: 44,
            border: '1px solid var(--border)',
            borderRadius: 15,
            background: '#fff',
            padding: '0 13px',
            outline: 'none',
            fontSize: 13,
            boxShadow: 'var(--shadow-card)',
          }}
        />
        <button
          type="submit"
          disabled={!canSend}
          style={{
            height: 44,
            border: 0,
            borderRadius: 15,
            background: canSend ? 'var(--primary)' : 'var(--surface-soft)',
            color: canSend ? '#fff' : 'var(--muted)',
            display: 'grid',
            placeItems: 'center',
          }}
        >
          <Send size={17} />
        </button>
      </form>
    </section>
  );
}
