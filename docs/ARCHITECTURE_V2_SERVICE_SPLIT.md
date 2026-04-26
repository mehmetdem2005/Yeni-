# Architecture v2 — Service Split

Bu belge, uygulamanın monolitik `services.py` yapısından temiz servis mimarisine geçişini tanımlar.

## Sorun

Önceki `services.py` çok fazla sorumluluk taşıyordu:

- Binance veri çekme
- Veri kaydetme
- Model eğitimi
- Coin analizi
- İndikatör/aile/özgüven/risk pipeline
- Sanal işlem açma
- Açık pozisyon güncelleme
- Haber çekme
- Log kayıtları

Bu yapı büyüdükçe hata ayıklamayı, test yazmayı ve cloud deployment’ı zorlaştırır.

## Yeni Yapı

```text
app.py
  ↓
services.py               → sadece orkestratör / facade
  ├── market_data_service.py
  ├── training_service.py
  ├── analysis_service.py
  ├── paper_trade_service.py
  ├── news_service.py
  └── service_utils.py
```

## Dosya Sorumlulukları

### service_utils.py

- Logları storage’a yazar.
- Binance public client çağrılarını rate-limit ile sarar.
- Rate-limit anahtarları endpoint bazlıdır.

Örnek:

```text
binance:klines:BTCUSDT:1h
binance:klines:ETHUSDT:1h
binance:book:BTCUSDT:50
```

### market_data_service.py

- Sadece piyasa verisi toplar.
- Mum verilerini SQLite’a kaydeder.
- Eğitim, analiz veya işlem açma yapmaz.

### training_service.py

- Sadece hafif modeli eğitir.
- Model state’i storage’a kaydeder.
- İşlem kararı vermez.

### analysis_service.py

- İndikatör, aile, işlem özgüveni ve risk planı üretir.
- Sanal işlem açmaz.
- Her coin için analiz payload’ı döndürür.

### paper_trade_service.py

- Analiz sonucu uygunsa sanal işlem açar.
- Açık pozisyonları SL/TP’ye göre günceller.
- Sanal bakiye ve equity kaydını yönetir.

### news_service.py

- Haber akışını çeker.
- Haberleri loglar.
- İşlem kararını doğrudan değiştirmez.

### services.py

- Tüm servisleri bir araya getirir.
- `cycle()` akışını yönetir.
- `status()` ile panele veri sağlar.

## Hedef

- Her dosya tek görev taşısın.
- Test yazmak kolay olsun.
- Termux-light çalışmaya devam etsin.
- Sonraki cloud/Supabase/Render ayrımı daha kolay olsun.
