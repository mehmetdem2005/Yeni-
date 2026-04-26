# V3 Product Blueprint — Profesyonel AI Kripto Kontrol Merkezi

Bu belge, kullanıcının son kararlarına göre uygulamanın V3 ürün mimarisini kilitler.

## 0. Kullanıcı Kararları

1. Ana ekranda her kritik bilgi görünsün ama küçük/kompakt olsun.
2. Grafikler TradingView/Binance benzeri gelişmiş yapıda olsun.
3. Balina takibi çok gelişmiş, çok katmanlı ve profesyonel olsun.
4. AI asistan dili ciddi analist + samimi konuşma karışımı olsun; kullanıcının konuşma tarzına uyum sağlasın.
5. Ana sayfa AI yorumu 10 dakikada bir yenilensin.
6. API keyler panelde Ayarlar sekmesinden girilebilsin.
7. İlk hedef Render + Supabase + Vercel cloud panel olsun.
8. 100 indikatör havuzu, balina, haber, çekirdek sinyaller, zaman aralıkları ve diğer bileşenler dahil edilsin.
9. Açık tema ana tema olsun; soft, rahat, Android Chrome uyumlu arayüz kullanılacak.
10. Haberler karar ağırlığına katılsın. Ancak haber tek başına işlem açtırmaz; haber ailesi destekleyici/risk azaltıcı bileşen olarak çalışır.

---

## 1. Yeni Ürün Tanımı

V3 hedefi yalnızca çalışan bir bot değil; mobilde rahat kullanılan, grafik odaklı, AI açıklamalı, ayarlanabilir ve cloud-ready bir kontrol merkezidir.

Ana hedefler:

- Android Chrome uyumlu mobil deneyim
- Soft açık tema
- Binance/TradingView benzeri grafik deneyimi
- Tüm kararların açıklanması
- Soru sorulabilir AI asistan
- 10 dakikada bir ana sayfa piyasa yorumu
- Gelişmiş haber ve balina aileleri
- Supabase + Render + Vercel mimarisi

---

## 2. Ana Sayfa Düzeni

Ana sayfa her şeyi gösterecek ama kartlar küçük ve kompakt olacak.

Üst bölüm:

- AI canlı piyasa yorumu
- Sistem Özgüveni = kapanmış işlemlerde başarı oranı
- Kanıt Gücü = kapanmış işlem sayısı ve güvenilirlik seviyesi
- Sanal bakiye
- Günlük / toplam kâr-zarar
- Açık işlem sayısı
- API/model/haber sağlığı küçük ikonlar

Ana sayfa kartları:

1. AI Piyasa Yorumu
2. Sistem Performansı
3. En Güçlü 3 Fırsat
4. Açık Pozisyonlar
5. Son Kararlar
6. Risk Uyarıları
7. Haber Etkisi
8. Balina / Emir Akışı Özeti

---

## 3. Sistem Özgüveni ve Kanıt Gücü

Sistem özgüveni kullanıcının tanımına göre hesaplanır:

```text
Sistem Özgüveni = Başarılı kapanan işlem / Toplam kapanan işlem
```

Örnekler:

```text
1 işlem, 1 başarılı = %100
5 işlem, 2 başarılı = %40
0 işlem = %0 / henüz ölçülmedi
```

Yanında mutlaka Kanıt Gücü gösterilir:

```text
Kanıt Gücü = min(kapanmış işlem sayısı / 100, 1.0)
```

Panel gösterimi:

```text
Sistem Özgüveni: %100
Kanıt Gücü: Çok düşük — sadece 1 işlem
```

Bu sayede 1/1 başarı matematiksel olarak %100 kalır ama istatistiksel güven şişirilmez.

---

## 4. Grafik Sistemi

Hedef: Binance/TradingView benzeri gelişmiş grafik.

Cloud/Vercel tarafında önerilen grafik motoru:

- TradingView Lightweight Charts

Termux/local fallback:

- Saf SVG grafikler

Grafik özellikleri:

- Gerçek mum grafiği
- Zaman dilimi seçimi: 1m, 5m, 15m, 1h, 4h, 1d, 1w
- EMA/SMA/MACD/RSI/ATR/Bollinger Bands vb. aç-kapat
- Hacim paneli
- Alt indikatör panelleri
- Giriş/çıkış noktaları
- SL/TP çizgileri
- Balina olay işaretleri
- Haber olay işaretleri
- Crosshair
- Zoom/pan
- Mobil touch uyumu

Her grafik kartında 3 nokta menüsü:

- Göster/gizle
- Renk ayarları
- Çizgi kalınlığı
- Zaman aralığı
- İndikatör ayarı
- Detay açıklaması

---

## 5. İndikatör Mimarisi

V1 çekirdekte aktif olanlar:

- EMA 50
- RSI 14
- ATR 14
- Hacim oranı

V3 hedefi: 100 indikatör havuzu.

Aileler:

1. Trend Ailesi
2. Momentum Ailesi
3. Volatilite / Risk Ailesi
4. Hacim / Likidite Ailesi
5. Rejim / Zaman Dilimi Ailesi
6. Yapay Zekâ Ailesi
7. Haber / Duygu Ailesi
8. Balina / Emir Akışı Ailesi
9. Destek / Direnç / Piyasa Yapısı Ailesi
10. İstatistik / Anomali Ailesi

Her indikatör şunları üretir:

- Ham değer
- Normalize skor 0-1
- Aile katkısı
- Grafik serisi
- Türkçe yorum
- Log kaydı

---

## 6. Balina / Emir Akışı Sistemi

Balina takibi çok katmanlı olacak.

Katmanlar:

1. Order book imbalance
2. Büyük emir duvarı tespiti
3. Ani emir duvarı ekleme/kaldırma
4. Büyük trade tespiti
5. Hacim patlaması
6. Likidite süpürme hareketi
7. Spread sıkışması/genişlemesi
8. Borsalar arası fiyat farkı, sonraki sürüm
9. On-chain cüzdan takibi, sonraki sürüm

Balina ailesi skor üretir:

```text
Balina Skoru = order_book_imbalance + büyük emir + büyük trade + hacim patlaması + likidite süpürme
```

Balina verisi tek başına alım yaptırmaz. İşlem özgüvenine ağırlıklı katkı verir veya risk azaltır.

---

## 7. Haber Sistemi

Kullanıcı kararı: haberler karar ağırlığına katılacak.

Ama güvenlik kuralı:

```text
Haber tek başına işlem açtırmaz.
Pozitif haber destekleyici katkı verir.
Negatif haber risk azaltır, miktarı küçültür veya işlemi engeller.
```

Haber ailesi kaynakları:

- RSS haber kaynakları
- Binance duyuruları
- Coin özel haber başlıkları
- Sonraki sürüm: sosyal medya / X / Reddit / on-chain duyurular

Her haber için:

- Kaynak
- Başlık
- İlgili coin
- Pozitif/nötr/negatif duygu
- Etki skoru
- Kaynak güven skoru
- AI yorumu
- Karara etkisi

---

## 8. AI Asistan ve 10 Dakikalık Yorum

Ana sayfada 10 dakikada bir AI piyasa yorumu üretilecek.

Dil:

- Ciddi analist + samimi konuşma karışımı
- Kullanıcının konuşma tarzına uyumlu
- Gerektiğinde benzetmelerle açıklar
- Gerçek para tavsiyesi vermez
- Sistemin verilerine erişir
- Emir açmaz, risk motorunu bypass etmez

Örnek:

```text
Kral, piyasa şu an sisli yolda araba sürmek gibi. BTC tarafında yön hafif toparlıyor ama hacim hâlâ tam destek vermiyor. Sistem bu yüzden acele etmiyor; daha temiz risk/ödül bekliyor.
```

Chatbot soruları:

- Neden işlem açmadı?
- BTC şu an neden zayıf/güçlü?
- Hangi indikatör baskın?
- Haberler riski artırıyor mu?
- Balina verisi ne söylüyor?
- Bu pozisyonun stopu neden burada?

---

## 9. API Key ve Ayarlar

Kullanıcı kararı: API keyler panelde Ayarlar sekmesinden girilebilsin.

Ayarlar sekmesi:

- Groq API Key
- Binance API Key, canlı emir kapalı varsayılan
- Supabase URL
- Supabase anon/service key ayrımı
- Haber kaynakları
- Rate-limit saniyesi
- Grafik tema ayarları
- Coin listesi
- Zaman dilimi listesi
- İndikatör aç/kapat
- Aile ağırlıkları

Güvenlik:

- API keyler frontend localStorage içinde açık tutulmamalı.
- Cloud sürümde backend secure environment veya Supabase vault benzeri çözüm kullanılmalı.
- Withdrawal yetkisi asla kullanılmamalı.

---

## 10. Cloud Mimari

İlk hedef cloud panel:

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

Servisler:

- Vercel: kullanıcı arayüzü, grafikler, chatbot UI
- Render API: auth, settings, status, assistant endpoint
- Render Worker: veri toplama, analiz, eğitim, paper-trade döngüsü
- Supabase: candles, signals, logs, paper trades, settings, news, whale events

---

## 11. Yeni Sekme Düzeni

Sekmeler rastgele değil, ürün mantığına göre ayrılır:

1. Ana Sayfa
2. Grafikler
3. Fırsatlar
4. Açık İşlemler
5. İndikatörler
6. Aileler
7. Balina / Emir Akışı
8. Haberler
9. AI Asistan
10. Backtest / Raporlar
11. Loglar
12. Ayarlar

Mobilde sekmeler yatay scroll değil, alt navigasyon veya hamburger menü ile düzenlenir.

---

## 12. Öncelikli Kodlama Sırası

1. Cloud settings ve Supabase schema planı
2. UI theme tokens: soft light tema
3. Vercel-ready frontend mimari planı
4. Backend API endpoint planı
5. AI assistant endpoint + 10 dk yorum cache
6. Indicator registry: 100 indikatör metadata havuzu
7. Whale engine v1: order book + volume + big trade
8. News engine v2: kaynak güveni + etki skoru
9. Chart data API: candles + overlays + markers
10. Dashboard V3 frontend

---

## 13. Kesin Kurallar

- LLM işlem açamaz.
- Haber tek başına işlem açamaz.
- Balina verisi tek başına işlem açamaz.
- Sistem özgüveni işlem başarı oranıdır.
- Kanıt gücü ayrıca gösterilir.
- Gerçek para bağlanmadan önce backtest + 60 gün paper trade gerekir.
- Withdrawal API yetkisi asla kullanılmaz.
