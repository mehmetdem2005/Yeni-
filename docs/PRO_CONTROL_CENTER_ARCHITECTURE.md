# Profesyonel Kontrol Merkezi Mimarisi

Bu belge, uygulamanın teknik kavramlarını net ayırır ve panel mimarisini kullanıcı dostu sekmelere böler.

## 1. Temel Kavramlar

Uygulamada birbirine karıştırılmaması gereken 4 ayrı puan vardır:

### 1.1 İndikatör Skoru

Bu, teknik göstergelerden gelen ham piyasa sinyalidir.

Örnek kaynaklar:

- EMA trend skoru
- RSI momentum skoru
- Hacim skoru
- ATR risk durumu

Gösterim adı:

```text
İndikatör Skoru
```

Anlamı:

```text
Piyasa teknik olarak alıma ne kadar uygun?
```

### 1.2 Yapay Zekâ Tahmini

Bu, modelin geçmiş verilerden öğrendiği olasılıktır.

Gösterim adı:

```text
Yapay Zekâ Tahmini
```

Anlamı:

```text
Model bu koşullarda olumlu sonuç ihtimalini yüzde kaç görüyor?
```

Bu değer indikatör skoru değildir. Ayrı gösterilir.

### 1.3 İşlem Özgüven Puanı

Bu, işlem açma kararına en yakın ana puandır.

Kaynakları:

- İndikatör skoru
- Yapay zekâ tahmini
- Büyük yön filtresi
- Günlük yön filtresi
- Likidite/spread durumu
- Risk/ödül kalitesi
- Açık pozisyon riski

Önerilen formül:

```text
İşlem Özgüveni =
    İndikatör Skoru × 0.30
  + Yapay Zekâ Tahmini × 0.30
  + Rejim Uyum Skoru × 0.15
  + Likidite Skoru × 0.10
  + Risk/Ödül Skoru × 0.10
  + Portföy Güvenliği Skoru × 0.05
```

Gösterim adı:

```text
İşlem Özgüveni
```

Anlamı:

```text
Bu sistem şu anda işlem açmaya ne kadar güveniyor?
```

### 1.4 Sistem Genel Özgüveni

Bu değer sağ üstte her zaman görünür.

Kaynakları:

- Son işlem performansı
- Model doğruluğu
- Güncel veri kalitesi
- Veri tazeliği
- Açık işlem riski
- Son hata durumu
- Piyasa kararsızlığı

Gösterim yeri:

```text
Sağ üst köşe: Sistem Özgüveni %72
```

Anlamı:

```text
Uygulamanın genel çalışma sağlığı ve karar kalitesi ne durumda?
```

## 2. Sekme Mimarisi

Tek ekrana her şeyi yığmak yok. Uygulama sekmelere ayrılır.

### 2.1 Ana Panel

Amaç: Kullanıcı ilk bakışta sistemi anlasın.

Gösterilecekler:

- Sağ üstte Sistem Özgüveni
- Sanal toplam para
- Günlük kâr/zarar
- Açık işlem sayısı
- Son karar
- Büyük ana butonlar
- Kâr grafiği

Butonlar:

- Başlat
- Durdur
- Bir Tur Çalıştır
- Sanal Hesabı Sıfırla

### 2.2 Piyasa Grafikleri Sekmesi

Amaç: Gerçek mum grafiklerini görmek.

Gösterilecekler:

- Coin seçimi
- Gerçek mum grafiği
- EMA çizgisi
- Alım noktaları
- Satış noktaları
- Stop-loss çizgisi
- Take-profit çizgisi

İlk sürümde mum grafiği SVG/HTML ile çizilir.
Sonraki sürümde Lightweight Charts veya Plotly benzeri grafik motoru eklenebilir.

### 2.3 İndikatörler Sekmesi

Amaç: Her indikatörün ne dediğini görmek.

Gösterilecekler:

- EMA 50 grafiği
- RSI 14 grafiği
- ATR 14 grafiği
- Hacim grafiği
- İndikatör Skoru grafiği

Her indikatör kartında:

- Değer
- Yorum
- Son 100 mum grafiği
- Al/Sat/Nötr etkisi

### 2.4 Aileler Sekmesi

Amaç: Tek tek indikatörler değil, aile kararlarını görmek.

Aileler:

- Trend Ailesi
- Momentum Ailesi
- Volatilite/Risk Ailesi
- Hacim/Likidite Ailesi
- Rejim/Piyasa Yönü Ailesi
- Yapay Zekâ Ailesi

Her aile için:

- Aile skoru
- Aile yorumu
- Katkı yüzdesi
- Son karar üzerindeki etkisi

### 2.5 Yapay Zekâ Sekmesi

Amaç: Modelin ne öğrendiğini göstermek.

Gösterilecekler:

- Eğitim örnek sayısı
- Son eğitim zamanı
- Model doğruluğu
- Pozitif örnek oranı
- Yapay zekâ tahmini grafiği
- Model en çok neye dikkat ediyor?

Teknik ağırlıklar kullanıcıya şöyle çevrilir:

- Kısa vadeli fiyat hareketine dikkat ediyor
- Hacim artışına dikkat ediyor
- Oynaklık yükselince temkinli oluyor
- Trend zayıfsa işlemden kaçıyor

### 2.6 Risk Yönetimi Sekmesi

Amaç: Girilecek miktar, stop-loss ve take-profit neden öyle seçildi görünsün.

Gösterilecekler:

- Akıllı pozisyon miktarı
- Maksimum işlem riski
- Stop-loss seviyesi
- Take-profit seviyesi
- Risk/ödül oranı
- Açık işlem riski
- Toplam portföy riski

### 2.7 Loglar Sekmesi

Loglar tek panelde karışmayacak. Alt sekmelere ayrılır.

Alt sekmeler:

1. Tüm Loglar
2. İndikatör Logları
3. Aile Logları
4. Yapay Zekâ Logları
5. İşlem Logları
6. Risk Logları
7. Veri Toplama Logları
8. Hata Logları
9. Haber Akışı Logları

## 3. Akıllı Pozisyon Miktarı Mimarisi

Sabit 250 USDT yerine akıllı miktar kullanılacak.

Girdi kaynakları:

- Sanal hesap büyüklüğü
- Stop mesafesi
- Sistem özgüveni
- İşlem özgüveni
- Volatilite
- Açık pozisyon riski
- Peş peşe kayıp durumu

Temel formül:

```text
Hesap_Riski = Sanal_Hesap × 0.005
Stop_Mesafesi_% = (Giriş - Stop) / Giriş
Ham_Pozisyon = Hesap_Riski / Stop_Mesafesi_%
Özgüven_Çarpanı = 0.50 ile 1.25 arası
Volatilite_Çarpanı = 0.50 ile 1.00 arası
Pozisyon = Ham_Pozisyon × Özgüven_Çarpanı × Volatilite_Çarpanı
Pozisyon = min(Pozisyon, Sanal_Hesap × 0.05)
```

Kullanıcıya gösterim:

```text
Sistem bu işlem için 187 USDT ayırdı.
Sebep: Sinyal orta-güçlü, stop mesafesi geniş, bu yüzden miktar azaltıldı.
```

## 4. Akıllı Stop-Loss Mimarisi

Stop-loss sabit değil, piyasa koşullarına göre hesaplanır.

Kaynaklar:

- ATR 14
- Son swing low
- Volatilite seviyesi
- Destek bölgesi
- Minimum risk/ödül filtresi

İlk sürüm formülü:

```text
ATR_Stop = Giriş - ATR × 1.5
Swing_Stop = Son anlamlı dip seviyesi
Stop = min(ATR_Stop, Swing_Stop) fakat aşırı uzaksa işlem iptal
```

Kurallar:

- Stop çok yakınsa işlem açılmaz
- Stop çok uzaksa pozisyon miktarı düşer
- Stop, risk bütçesini bozarsa işlem açılmaz

## 5. Akıllı Take-Profit Mimarisi

TP rastgele değil, risk/ödül ve dirençle belirlenir.

Kaynaklar:

- Risk mesafesi
- Yakın direnç
- Son swing high
- ATR tabanlı hedef
- Minimum 1:2 risk/ödül kuralı

İlk sürüm formülü:

```text
Ham_TP = Giriş + Risk_Mesafesi × 3
Direnç_TP = Giriş üstündeki en yakın direnç
TP = min(Ham_TP, Direnç_TP) eğer gerçek R/R >= 2 ise
Aksi halde işlem açılmaz
```

Kullanıcıya gösterim:

```text
Kâr al seviyesi 103.250 olarak seçildi.
Sebep: Direnç bu bölgede ve risk/ödül oranı 1:2 üstünde kalıyor.
```

## 6. Haber Akışı Sekmesi

İlk sürümde haber akışı basit tutulur.

Kaynaklar:

- RSS destekli kripto haberleri
- Binance duyuruları
- Coin özel haber akışı

Haberler işlem kararını doğrudan değiştirmez. İlk aşamada sadece kullanıcıya gösterilir.

Sonraki aşama:

- Haber sınıflandırma
- Negatif/pozitif duygu analizi
- Ani haber risk filtresi

## 7. Canlı Grafikler

Grafikler gerçek veriden üretilecek.

İlk grafikler:

- Mum grafiği
- Fiyat çizgisi
- EMA çizgisi
- RSI çizgisi
- ATR çizgisi
- Hacim barları
- Sanal para çizgisi
- Model tahmini çizgisi
- Sistem özgüveni çizgisi

## 8. Karar Pipeline'ı

Karar akışı ekranda gösterilecek.

```text
Veri Geldi
↓
İndikatörler Hesaplandı
↓
Aile Skorları Oluştu
↓
Yapay Zekâ Tahmini Üretildi
↓
Risk Motoru Miktar/SL/TP Hesapladı
↓
İşlem Özgüveni Hesaplandı
↓
Sistem Kararı Verildi
```

Her adım yeşil/sarı/kırmızı durumla gösterilir.

## 9. Yeni Dosya Mimarisi

Eklenecek modüller:

```text
indicator_engine.py       → gösterge hesapları + gösterge logları
family_engine.py          → aile skorları + aile logları
confidence_engine.py      → işlem özgüveni + sistem özgüveni
smart_risk_engine.py      → akıllı miktar + akıllı SL/TP
tabbed_dashboard.py       → sekmeli web panel
chart_renderer.py         → SVG mum/fiyat/RSI/ATR/hacim grafikleri
news_feed.py              → haber akışı
log_channels.py           → logları kanallara ayırma
```

## 10. Uygulama Önceliği

Aşama 1:

- İşlem özgüveni
- Sistem özgüveni
- Sağ üst özgüven göstergesi
- Akıllı miktar
- Akıllı SL/TP açıklaması

Aşama 2:

- Sekmeli panel
- İndikatör logları
- Aile logları
- Tüm loglar

Aşama 3:

- Mum grafikleri
- İndikatör grafikleri
- Sanal para grafiği

Aşama 4:

- Haber akışı sekmesi
- Asistan açıklama paneli

## 11. Tasarım İlkesi

Hiçbir alan muğlak olmayacak.

Her önemli değer için üç şey yazılacak:

1. Değer
2. Ne anlama geldiği
3. Karara etkisi

Örnek:

```text
İşlem Özgüveni: %74
Anlamı: Sistem bu işlemi açmaya oldukça yakın.
Etkisi: %70 üstü ise risk motoru onaylarsa sanal işlem açılabilir.
```
