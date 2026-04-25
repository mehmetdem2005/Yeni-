# İndikatör ve Grafik Paneli Mimarisi

Bu belge, uygulamanın kullanıcı dostu ve gelişmiş gösterge paneline dönüşmesi için kurulacak mimariyi tanımlar.

Amaç: Kullanıcı teknik terimlere boğulmadan; fiyatı, indikatörleri, yapay zekâ skorunu, sanal para performansını ve sistemin karar gerekçesini aynı ekranda görebilsin.

## 1. Ana Ekran Yapısı

Uygulama 6 ana panele ayrılır:

1. Genel Durum Paneli
2. Sanal Para ve Kâr/Zarar Paneli
3. Coin Grafik Paneli
4. İndikatör Paneli
5. Yapay Zekâ Eğitim Paneli
6. Canlı Akış ve Açıklama Paneli

## 2. Genel Durum Paneli

Bu panel teknik terimleri gizler ve sistemi sade anlatır.

Gösterilecek bilgiler:

- Sistem çalışıyor mu?
- Son veri toplama zamanı
- Toplanan mum sayısı
- Model kaç örnekle eğitildi?
- Bugünkü işlem sayısı
- Açık sanal işlem var mı?
- Sanal hesap toplam değeri

Kullanıcıya gösterilecek sade dil:

- "Piyasa verisi toplanıyor"
- "Yapay zekâ eğitiliyor"
- "Sistem fırsat arıyor"
- "Sanal işlem açık"
- "Şu an işlem için yeterli sinyal yok"

## 3. Sanal Para ve Performans Paneli

Başlangıç sanal para: 10.000 USDT

Gösterilecek metrikler:

- Toplam sanal para
- Nakit bakiye
- Açık işlem değeri
- Toplam kâr/zarar
- Kâr/zarar yüzdesi
- Kapanan işlem sayısı
- Kazanan işlem sayısı
- Kaybeden işlem sayısı
- Başarı oranı
- Ortalama kâr
- Ortalama zarar

Grafikler:

- Sanal para çizgi grafiği
- Günlük kâr/zarar grafiği
- İşlem başına kâr/zarar grafiği

## 4. Coin Grafik Paneli

Her coin için ayrı kart olacak.

Desteklenecek coinler:

- BTC/USDT
- ETH/USDT
- BNB/USDT
- SOL/USDT

Her kartta:

- Güncel fiyat
- Son 24 saat yönü
- Sinyal gücü
- Yapay zekâ olumlu ihtimal yüzdesi
- Büyük yön: olumlu/zayıf
- Günlük yön: olumlu/zayıf
- Sistem kararı: izle / sanal alım adayı / işlem açık

Grafikler:

- Fiyat çizgi grafiği
- EMA 50 çizgisi
- Alım noktaları
- Satış noktaları
- Zarar kes seviyesi
- Kâr al seviyesi

Teknik terim gösterimi:

- Bid yerine: Piyasanın alış fiyatı
- Ask yerine: Piyasanın satış fiyatı
- W1 yerine: Büyük yön
- D1 yerine: Günlük yön
- H1 yerine: Saatlik analiz
- ML yerine: Yapay zekâ tahmini

## 5. İndikatör Paneli

İndikatörler gizli kalmayacak; kullanıcı hem değerini hem grafiğini görecek.

v1 göstergeleri:

1. EMA 50
2. RSI 14
3. ATR 14
4. Hacim oranı
5. Sinyal gücü
6. Yapay zekâ tahmini

Her indikatör için 3 şey gösterilir:

- Güncel değer
- Basit yorum
- Küçük grafik

Örnek:

RSI:

- Değer: 54
- Yorum: Momentum dengeli
- Grafik: Son 100 mum RSI çizgisi

ATR:

- Değer: 220 USDT
- Yorum: Risk mesafesi orta
- Grafik: Volatilite çizgisi

EMA 50:

- Yorum: Fiyat ortalamanın üstünde ise yön olumlu
- Grafik: Fiyat + EMA çizgisi

Hacim:

- Yorum: Son hacim normalin üstünde/altında
- Grafik: Hacim çubukları

## 6. Yapay Zekâ Eğitim Paneli

Bu panel kullanıcıya modelin gerçekten eğitildiğini gösterir.

Gösterilecekler:

- Eğitim durumu
- Eğitim örnek sayısı
- Son eğitim zamanı
- Model doğruluk oranı
- Olumlu örnek oranı
- Model ağırlıkları kullanıcı dostu açıklamayla

Model ağırlıkları teknik haliyle gösterilmeyecek. Şöyle çevrilecek:

- Son fiyat hareketi ne kadar önemli?
- Hacim artışı ne kadar etkili?
- Volatilite riski ne kadar etkili?
- Trend farkı ne kadar etkili?

Örnek açıklama:

"Model şu anda en çok hacim artışına ve kısa vadeli fiyat momentumuna dikkat ediyor."

## 7. Canlı Akış ve Asistan Paneli

Bu panel sistemin ne yaptığını Türkçe anlatır.

Örnek akış:

- 14:05 — BTC verisi toplandı.
- 14:05 — ETH verisi toplandı.
- 14:06 — Yapay zekâ 438 örnekle yeniden eğitildi.
- 14:06 — BTC için sinyal zayıf, işlem açılmadı.
- 14:06 — SOL için günlük yön zayıf, işlem açılmadı.
- 14:07 — Sanal hesap değeri güncellendi.

Asistan açıklamaları:

- "Neden işlem açmadı?"
- "Bu indikatör ne demek?"
- "Şu an sistem ne bekliyor?"
- "Kâr neden düştü?"

İlk sürümde asistan statik açıklama üretir. Sonraki sürümde gerçek sohbet paneli eklenir.

## 8. Grafik Mimarisi

Telefon uyumu için ağır grafik kütüphanesi kullanılmayacak.

İlk aşama:

- Saf HTML + SVG grafikler
- JavaScript gerekirse çok küçük tutulur
- Veri tarayıcıya JSON olarak gönderilir
- Grafikler cihazda çizilir

Grafik türleri:

1. Çizgi grafik: fiyat, EMA, sanal para
2. Bar grafik: hacim, işlem kâr/zarar
3. Gauge/puan barı: sinyal gücü, yapay zekâ tahmini
4. Seviye çizgileri: SL ve TP

## 9. Backend Mimarisi

Mevcut yapı korunur ama genişletilir:

```text
Binance Public Data
    ↓
Veri Toplama Servisi
    ↓
SQLite Depolama
    ↓
İndikatör Hesaplama Servisi
    ↓
Hafif ML Eğitim Servisi
    ↓
Karar Motoru
    ↓
Sanal İşlem Motoru
    ↓
Panel API
    ↓
Türkçe Web Arayüzü
```

## 10. Yeni Modüller

Eklenecek dosyalar:

```text
src/crypto_paper_bot/indicator_engine.py
src/crypto_paper_bot/chart_data.py
src/crypto_paper_bot/explainer.py
src/crypto_paper_bot/dashboard_sections.py
```

Görevleri:

### indicator_engine.py

- EMA hesaplar
- RSI hesaplar
- ATR hesaplar
- Hacim oranı hesaplar
- Her indikatör için yorum üretir

### chart_data.py

- Fiyat grafiği verisi üretir
- EMA grafiği verisi üretir
- RSI grafiği verisi üretir
- Hacim grafiği verisi üretir
- Sanal para grafiği verisi üretir

### explainer.py

- Teknik kararları Türkçe açıklar
- İşlem açılmama nedenlerini açıklar
- İndikatörleri basit dille anlatır

### dashboard_sections.py

- HTML kartlarını üretir
- Grafik SVG'lerini üretir
- Teknik veriyi kullanıcı dostu metne çevirir

## 11. Kullanıcı Deneyimi İlkeleri

- Kod/JSON görünmeyecek
- İngilizce teknik kısaltmalar gizlenecek veya Türkçeye çevrilecek
- Her metrik yanında kısa açıklama olacak
- Her kararın nedeni yazacak
- Grafikler basit ve okunabilir olacak
- Mobil ekranda önce para durumu, sonra canlı kararlar, sonra grafikler gelecek
- Gelişmiş veriler ayrı açılır panelde gösterilecek

## 12. Uygulama Aşamaları

Aşama 1:

- İndikatör motoru
- Grafik veri üretimi
- Türkçe açıklama motoru

Aşama 2:

- Panel tasarımı yenileme
- Fiyat + EMA grafiği
- RSI grafiği
- ATR grafiği
- Hacim grafiği

Aşama 3:

- Sanal para grafikleri
- İşlem geçmişi grafikleri
- Başarı oranı grafikleri

Aşama 4:

- Asistan açıklama paneli
- "Neden işlem açmadı?" cevapları
- "Bu gösterge ne demek?" cevapları

## 13. Son Hedef

Kullanıcı uygulamayı açtığında şunları net görmeli:

- Param artıyor mu azalıyor mu?
- Sistem şu an ne yapıyor?
- Hangi coinleri izliyor?
- Neden işlem açtı veya açmadı?
- Hangi indikatör ne söylüyor?
- Yapay zekâ neye göre karar veriyor?
- Grafiklerde trend nasıl görünüyor?
