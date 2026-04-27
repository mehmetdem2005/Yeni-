# Crypto Spot Bot — Paper Trade Control Center

Bu repo, **canlı para için değil**, paper-trade, veri toplama, grafik, haber, AI asistan ve otomasyon kontrol paneli için tasarlanmış kripto spot bot sistemidir.

## Güvenlik Durumu

- Spot only
- Long only
- Kaldıraç yok
- Short yok
- Withdrawal yetkisi kullanılmaz
- Varsayılan mod paper-trade
- Gerçek emir göndermek için hazır değildir
- Önce uzun süre paper-trade, backtest ve walk-forward test gerekir

Bu yazılım finansal tavsiye değildir.

---

## Ana Mimari

```text
Frontend: Next.js mobil panel
Backend: FastAPI API servisi
Worker: Render background worker
Database: Supabase/Postgres veya lokal SQLite
AI: Groq router/asistan
Market Data: Binance public market endpoints
```

Sistem iki farklı çalışma yoluna sahiptir:

```text
1. Web panel içi manuel kontrol
   - Başlat
   - Durdur
   - Tek Tur
   - Veri Topla
   - Eğit
   - Acil Kapat
   - Sıfırla

2. Ayrı worker otomasyonu
   - Render worker içinde düzenli cycle çalıştırır
   - heartbeat bilgisini veritabanına yazar
   - panel worker durumunu görebilir
```

---

## Sayfalar

```text
/             Ana sayfa kontrol paneli
/charts       Mum grafikleri, indikatörler, markerlar
/portfolio    Sanal bakiye, açık pozisyonlar, işlem geçmişi
/logs         Canlı loglar, haberler, asistan önizleme
/news         Haber akışı ve duygu/etki analizi
/settings     Runtime, API, güvenlik ve panel ayarları
/assistant    AI asistan sohbet ekranı
```

---

## Lokal Backend Çalıştırma

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-cloud.txt
python -m pip install -e .
python scripts/smoke_cloud_runtime.py
uvicorn crypto_paper_bot.api_server:app --host 0.0.0.0 --port 8000
```

Backend sağlık kontrolü:

```bash
curl http://localhost:8000/health
```

API durum kontrolü:

```bash
curl http://localhost:8000/api/status
```

---

## Lokal Frontend Çalıştırma

```bash
cd frontend
npm install
npm run dev
```

Frontend varsayılan olarak şuna bağlanır:

```text
http://localhost:8000
```

Cloud ortamda frontend için API adresi Vercel environment alanına girilmelidir:

```text
NEXT_PUBLIC_API_BASE_URL=https://render-api-adresin
```

---

## Worker Çalıştırma

Lokal worker:

```bash
python -m crypto_paper_bot.worker
```

Paket script ile:

```bash
crypto-paper-bot-worker
```

Worker şunları yapar:

```text
services.cycle() çalıştırır
veri toplar
eğitim yapar
sistem özgüveni hesaplar
analiz üretir
paper pozisyonları yönetir
haberleri çeker
runtime heartbeat kaydeder
```

---

## Supabase Kurulum

1. Supabase projesi oluştur.
2. SQL Editor aç.
3. Şu dosyanın tamamını çalıştır:

```text
supabase/schema.sql
```

Bu şema şunları oluşturur:

```text
candles
signal_log
paper_wallets
paper_positions
equity_points
news_items
whale_events
event_logs
app_settings
assistant_messages
ai_commentary
backtest tabloları
```

Not: İlk özel/admin deploy aşamasında backend service role ile çalışır. Public frontend doğrudan Supabase’e yazmamalıdır.

---

## Render Deploy

Repo içinde blueprint hazırdır:

```text
render.yaml
```

İki servis tanımlar:

```text
crypto-paper-bot-api      FastAPI web servisi
crypto-paper-bot-worker   background worker servisi
```

Render Web Service komutu:

```bash
uvicorn crypto_paper_bot.api_server:app --host 0.0.0.0 --port $PORT
```

Render Worker komutu:

```bash
python -m crypto_paper_bot.worker
```

Render environment alanlarında backend için şu değişkenler tanımlanmalıdır:

```text
APP_ENV
MIN_API_INTERVAL_SECONDS
DATABASE_URL
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_KEY
GROQ_API_KEY
BINANCE_ENABLE_LIVE_TRADING
BINANCE_ENABLE_WITHDRAWALS
```

Güvenlik için:

```text
BINANCE_ENABLE_LIVE_TRADING=false
BINANCE_ENABLE_WITHDRAWALS=false
```

---

## Vercel Deploy

Frontend klasörü:

```text
frontend
```

Build komutu:

```bash
npm run build
```

Start/dev komutu:

```bash
npm run dev
```

Vercel environment alanında şunu tanımla:

```text
NEXT_PUBLIC_API_BASE_URL=https://render-api-adresin
```

---

## Smoke Check

Cloud runtime hızlı test:

```bash
python scripts/smoke_cloud_runtime.py
```

Başarılı örnek çıktı:

```json
{
  "ok": true,
  "database": {
    "backend": "postgres"
  },
  "db_rows": 1200,
  "wallet_cash": 10000,
  "open_count": 0,
  "system_confidence": 0.4,
  "worker": null
}
```

---

## Önemli Çekirdek Kurallar

```text
W1: ana rejim kapısı
D1: günlük yön kapısı
H1: giriş sinyali
ATR: puana girmez; SL, TP ve pozisyon büyüklüğü için kullanılır
İşlem özgüveni: çok bileşenli skor
Sistem özgüveni: geçmiş paper-trade başarısına göre yorumlanır
```

---

## ML/Data Pipeline Notu

Gelecek aşama için plan şurada tutulur:

```text
docs/ML_DATA_PIPELINE_PLAN.md
```

Bu aşama henüz aktif implementasyon değildir. Önce UI, API, Supabase, worker ve paper-trade veri toplama stabil hale getirilmelidir.
