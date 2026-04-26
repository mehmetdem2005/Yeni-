# Cloud-First Policy

Bu proje V3 aşamasından itibaren Termux odaklı değildir.

## Ana hedef

Ana hedef üretim mimarisi şudur:

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

## Termux'un yeri

Termux yalnızca şu amaçlarla tutulur:

- hızlı lokal smoke test
- telefonda acil kontrol
- geliştirme fallback'i
- eski hafif prototipi çalıştırma

Termux artık mimari kararların merkezi değildir.

## Bundan sonra kodlama önceliği

Öncelik sırası:

1. Supabase/Postgres runtime storage
2. Render API server
3. Render background worker
4. Vercel frontend
5. Settings API ve güvenli secret yönetimi
6. Chart data API
7. TradingView/Binance benzeri grafik paneli
8. AI assistant endpoint
9. 10 dakikalık ana sayfa AI yorumu
10. Haber ağırlık motoru
11. Balina / emir akışı motoru
12. 100 indikatör registry
13. Backtest ve rapor ekranı

## Yasaklanan yön kayması

Bundan sonra kullanıcı açıkça istemedikçe cevapların ve kodlama planının merkezi şunlar olmayacak:

- Termux kurulumu
- Android paket sorunları
- telefondan lokal panel açma
- local-only SQLite akışı

Bu konular sadece uyumluluk notu olarak kalabilir.

## Cloud-first kalite kuralı

Her yeni modül şu sorulara göre yazılır:

1. Supabase/Postgres'e bağlanabilir mi?
2. Render worker içinde sürekli çalışabilir mi?
3. Vercel frontend bu veriyi API üzerinden okuyabilir mi?
4. Mobil Android Chrome'da rahat gösterilebilir mi?
5. API key veya secret frontend'e sızıyor mu?
6. Gerçek para açmadan paper-trade güvenlik sınırlarını koruyor mu?

## Sistem hedefi

Bu proje basit terminal botu değil; cloud üzerinde çalışan, mobil uyumlu, grafik odaklı, AI açıklamalı, haber/balina/indikatör ağırlıklı profesyonel paper-trade kontrol merkezidir.
