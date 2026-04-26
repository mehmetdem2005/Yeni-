# V3 Cloud Deployment Guide

Bu belge V3 hedef mimari için ilk deployment yolunu anlatır.

## Mimari

```text
Vercel Frontend
  ↓
Render API Server
  ↓
Supabase Postgres
  ↑
Render Background Worker
  ↑
Binance / Groq / Haber / Balina kaynakları
```

## 1. Supabase

1. Supabase projesi oluştur.
2. SQL Editor aç.
3. `supabase/schema.sql` içeriğini çalıştır.
4. Project Settings → Database kısmından pooled Postgres connection string al.
5. Bu değeri Render’da `DATABASE_URL` olarak gir.

Önemli:

- İlk aşamada backend service role ile çalışır.
- Frontend doğrudan service key görmemeli.
- RLS açık bırakıldı; public frontend erişim politikaları ayrıca yazılmalı.

## 2. Render

`render.yaml` iki servis tanımlar:

1. `crypto-paper-bot-api`
   - Web/API panel servisi
   - `python -m crypto_paper_bot.app`

2. `crypto-paper-bot-worker`
   - Arka plan veri toplama ve paper-trade döngüsü
   - `python -m crypto_paper_bot.worker`

Render environment değişkenleri:

```text
APP_ENV=render
DATABASE_URL=...
SUPABASE_URL=...
SUPABASE_SERVICE_KEY=...
GROQ_API_KEY=...
BINANCE_ENABLE_LIVE_TRADING=false
BINANCE_ENABLE_WITHDRAWALS=false
MIN_API_INTERVAL_SECONDS=10
WORKER_CYCLE_SECONDS=600
```

## 3. Vercel

Vercel frontend sonraki fazdır.

Planlanan frontend:

```text
frontend/
  app/
  components/
  lib/
  charts/
```

Vercel env:

```text
NEXT_PUBLIC_API_BASE_URL=https://crypto-paper-bot-api.onrender.com
```

Vercel frontend backend API üzerinden veri alır. Secret key görmez.

## 4. Termux ve Cloud ayrımı

Termux-light hâlâ çalışır:

```bash
python -m pip install -e .
python -m crypto_paper_bot.app
```

Cloud full:

```bash
pip install -r requirements-cloud.txt
pip install -e .
python -m crypto_paper_bot.app
```

## 5. Güvenlik kuralları

- Withdrawal key asla kullanılmaz.
- Live trading varsayılan kapalıdır.
- Groq işlem açamaz.
- Haber tek başına işlem açamaz.
- Balina verisi tek başına işlem açamaz.
- Canlı para için backtest + 60 gün paper trade şarttır.

## 6. Sıradaki eksikler

1. `database_adapter.py`: SQLite ve Supabase/Postgres arasında gerçek adaptör.
2. FastAPI/ASGI server: Render production için daha doğru API.
3. Vercel frontend.
4. Chart data API.
5. AI assistant endpoint.
6. Settings API.
7. Whale engine.
8. 100 indikatör registry.
