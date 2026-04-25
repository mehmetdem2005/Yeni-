# Adaptif Özgüven, Rate Limit ve Groq Model Yönlendirme Mimarisi

Bu belge, işlem özgüveni formülünün sabit kalmaması, API isteklerinin rate-limit yememesi ve yapay zekâ model çağrılarının Groq üzerinde akıllı şekilde yönlendirilmesi için mimariyi tanımlar.

## 1. Rate Limit İlkesi

Hiçbir dış servis isteği 10 saniyeden daha sık yapılmaz.

Varsayılan kural:

```text
Minimum istek aralığı = 10 saniye
```

Eğer hata alınırsa:

```text
1. hata → 20 saniye bekle
2. hata → 40 saniye bekle
3. hata → 80 saniye bekle
4. hata → ilgili kaynağı geçici pasifleştir
```

Kullanım alanları:

- Binance veri çekme
- Haber akışı çekme
- Groq model çağrısı
- Her türlü harici API

Panelde gösterilecek:

```text
API Sağlığı: Normal
Son istek: 14 saniye önce
Bekleme süresi: 10 saniye
Son hata: Yok
```

## 2. Groq Model Yönlendirme Mimarisi

Sistem, yapay zekâ çağrılarında önce en güçlü modelden başlar.

Ancak model isimleri zamanla değişebileceği için model sırası config dosyasından okunur.

Örnek yapı:

```text
primary_model = listedeki ilk model
fallback_model_1 = listedeki ikinci model
fallback_model_2 = listedeki üçüncü model
```

Davranış:

```text
1. Önce en güçlü model denenir.
2. Kota/rate-limit/hata gelirse model cooldown'a alınır.
3. Sonraki modele geçilir.
4. Tüm modeller hata verirse yapay zekâ açıklaması yerine yerel açıklama motoru kullanılır.
```

Önemli:

```text
Groq modeli işlem açma yetkisine sahip değildir.
Groq sadece açıklama, özetleme, haber sınıflandırma ve kullanıcı yardım paneli için kullanılır.
İşlem kararını risk motoru ve yerel skor sistemi verir.
```

## 3. Sabit Formül Yeterli mi?

Başlangıç için evet, kalıcı sistem için hayır.

Başlangıç formülü:

```text
İşlem Özgüveni =
    İndikatör Skoru × 0.30
  + Yapay Zekâ Tahmini × 0.30
  + Rejim Uyum Skoru × 0.15
  + Likidite Skoru × 0.10
  + Risk/Ödül Skoru × 0.10
  + Portföy Güvenliği Skoru × 0.05
```

Bu formül ilk çalıştırma için güvenli varsayımdır. Fakat sistem veri topladıkça ağırlıklar başarı oranlarına göre ayarlanmalıdır.

## 4. Adaptif Ağırlık Sistemi

Her bileşen için ayrı başarı kaydı tutulur:

- İndikatör Skoru
- Yapay Zekâ Tahmini
- Rejim Uyum Skoru
- Likidite Skoru
- Risk/Ödül Skoru
- Portföy Güvenliği Skoru

Her bileşen için şu veriler tutulur:

```text
Toplam katkı yaptığı işlem sayısı
Kazandırdığı işlem sayısı
Kaybettirdiği işlem sayısı
Ortalama kâr/zarar
Son başarı oranı
```

Başarı oranı:

```text
Başarı = Kazanan İşlem / Toplam İşlem
```

Ama tek başına başarı oranı yeterli değildir. Çünkü az örneği olan bileşen aşırı şişebilir.

Bu yüzden güvenilirlik düzeltmesi uygulanır:

```text
Düzeltilmiş Başarı = (Kazanan + 1) / (Toplam + 2)
```

Bu, veri azsa skoru 0.50'ye yakın tutar.

## 5. Ağırlık Güncelleme

Ağırlıklar doğrudan rastgele değişmez. Önce her bileşenin düzeltilmiş başarısı hesaplanır.

Sonra aritmetik ortalama ve normalizasyon yapılır:

```text
Bileşen_Ham_Ağırlığı = Başlangıç_Ağırlığı × Düzeltilmiş_Başarı
Toplam = tüm Ham_Ağırlıkların toplamı
Yeni_Ağırlık = Bileşen_Ham_Ağırlığı / Toplam
```

Koruma sınırları:

```text
Hiçbir bileşen %5 altına düşemez.
Hiçbir bileşen %45 üstüne çıkamaz.
```

Bu sayede sistem tek bir bileşene körü körüne bağlanmaz.

## 6. İşlem Özgüveni Hesaplama

Yeni adaptif formül:

```text
İşlem Özgüveni =
    İndikatör Skoru × Adaptif_İndikatör_Ağırlığı
  + Yapay Zekâ Tahmini × Adaptif_AI_Ağırlığı
  + Rejim Uyum Skoru × Adaptif_Rejim_Ağırlığı
  + Likidite Skoru × Adaptif_Likidite_Ağırlığı
  + Risk/Ödül Skoru × Adaptif_RiskÖdül_Ağırlığı
  + Portföy Güvenliği Skoru × Adaptif_Portföy_Ağırlığı
```

Panelde gösterilecek:

```text
İşlem Özgüveni: %74
En çok katkı veren: İndikatör Skoru
En zayıf katkı: Likidite
Ağırlıklar başarıya göre otomatik ayarlanıyor.
```

## 7. Sistem Genel Özgüveni

Sağ üstte görünen sistem özgüveni işlem özgüveninden ayrıdır.

Kaynakları:

- Veri tazeliği
- Son API hataları
- Model doğruluğu
- Sanal hesap performansı
- Açık işlem riski
- Son kayıp serisi

Örnek formül:

```text
Sistem Özgüveni =
    Veri Sağlığı × 0.25
  + Model Sağlığı × 0.20
  + API Sağlığı × 0.20
  + Sanal Hesap Performansı × 0.20
  + Risk Sağlığı × 0.15
```

Bu değer sağ üstte gösterilir.

## 8. Akıllı Miktar Bağlantısı

Sabit miktar kaldırılır.

Pozisyon miktarı şunlara göre ayarlanır:

- Sanal hesap büyüklüğü
- Stop mesafesi
- İşlem özgüveni
- Sistem özgüveni
- Volatilite
- Açık işlem riski

Formül:

```text
Hesap_Riski = Sanal_Hesap × 0.005
Ham_Pozisyon = Hesap_Riski / Stop_Mesafesi_%
İşlem_Çarpanı = 0.50 + İşlem_Özgüveni
Sistem_Çarpanı = 0.50 + Sistem_Özgüveni / 2
Pozisyon = Ham_Pozisyon × İşlem_Çarpanı × Sistem_Çarpanı
Pozisyon = min(Pozisyon, Sanal_Hesap × 0.05)
```

Panelde:

```text
Sistem bu işlem için 186 USDT ayırdı.
Sebep: İşlem özgüveni yüksek ama volatilite yüksek olduğu için miktar azaltıldı.
```

## 9. Loglama

Her özgüven hesabı loglanır.

Log kanalları:

- confidence_log
- rate_limit_log
- groq_router_log
- adaptive_weight_log
- smart_position_log

Her logda:

```text
Zaman
Bileşen skorları
Kullanılan ağırlıklar
Nihai özgüven
Açıklama
```

## 10. Uygulama Aşaması

İlk kodlanacak dosyalar:

```text
rate_limiter.py
llm_router.py
adaptive_confidence.py
```

Sonraki adımda bu modüller panel ve karar motoruna bağlanır.
