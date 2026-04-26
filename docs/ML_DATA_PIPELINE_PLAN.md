# ML / Data Pipeline Architecture Plan

Bu belge ileriki aşama için nottur. Şu an uygulanmayacak. Mevcut öncelik beyaz mobil UI, frontend sayfaları, FastAPI endpointleri, Supabase/Render/Vercel uyumu ve paper-trade panelinin tamamlanmasıdır.

## Amaç

Sistem ileride gerçek bir veri bilimi ve makine öğrenmesi hattına sahip olacak:

```text
Ham piyasa verisi
  ↓
Pandas ile okuma ve temizleme
  ↓
Matplotlib ile grafik ve anomali görselleştirme
  ↓
NumPy ile model girdisi sayı dizileri
  ↓
Scikit-Learn / PyTorch ile model eğitimi
  ↓
Scikit-Learn metrikleri ile doğruluk ölçümü
  ↓
Model skorunun işlem özgüveni hesabına kontrollü katkısı
```

---

## 1. Pandas Katmanı — Veri Okuma ve Temizleme

### Görev

Pandas, ham veriyi tablo haline getirip temizlemek için kullanılacak.

### Kullanım alanları

- OHLCV mum verisini DataFrame olarak okumak
- Eksik mumları tespit etmek
- Tekrarlı satırları silmek
- Zaman kolonunu UTC datetime formatına çevirmek
- Fiyat ve hacim kolonlarını numeric hale getirmek
- NaN / inf değerleri temizlemek
- Train / validation / test bölmeleri üretmek
- Feature tablosu hazırlamak

### Planlanan modül

```text
src/crypto_paper_bot/ml/dataframe_cleaning.py
```

### Ana fonksiyonlar

```text
load_candles_to_dataframe()
clean_ohlcv_dataframe()
validate_candle_continuity()
remove_outliers_basic()
create_train_validation_test_split()
```

---

## 2. Matplotlib Katmanı — Görselleştirme ve Anomali Analizi

### Görev

Matplotlib, model eğitimi öncesinde veriyi insan gözüyle kontrol etmek için kullanılacak.

### Kullanım alanları

- Fiyat grafiği çizmek
- Hacim grafiği çizmek
- RSI / MACD / ATR gibi indikatörleri görselleştirmek
- Anormal hacim patlamalarını işaretlemek
- Aşırı volatilite mumlarını işaretlemek
- Eğitim öncesi veri raporu üretmek

### Planlanan modül

```text
src/crypto_paper_bot/ml/visual_diagnostics.py
```

### Ana fonksiyonlar

```text
plot_close_price()
plot_volume_spikes()
plot_indicator_panels()
plot_anomaly_report()
save_training_diagnostic_charts()
```

### Not

Bu grafikler kullanıcı arayüzündeki canlı chart için değil, eğitim ve veri kalitesi raporu için kullanılacak. Canlı UI grafikleri Next.js + lightweight-charts ile devam edecek.

---

## 3. NumPy Katmanı — Sayısal Dizi ve Tensor Hazırlığı

### Görev

NumPy, temizlenmiş tabloyu modelin anlayacağı sayısal dizilere dönüştürmek için kullanılacak.

### Kullanım alanları

- Feature matrix oluşturmak
- Label vector oluşturmak
- Sliding window üretmek
- Normalize edilmiş sayı dizileri hazırlamak
- Train/test array ayırmak
- PyTorch tensorlarına geçiş öncesi veri hazırlamak

### Planlanan modül

```text
src/crypto_paper_bot/ml/feature_arrays.py
```

### Ana fonksiyonlar

```text
build_feature_matrix()
build_label_vector()
make_sliding_windows()
standardize_features()
convert_to_numpy_arrays()
```

---

## 4. Feature Engineering Katmanı

### Görev

Modelin ham fiyat yerine anlamlı piyasa özellikleriyle eğitilmesini sağlar.

### Kullanılacak özellik aileleri

```text
Trend:
- EMA uzaklığı
- EMA eğimi
- fiyat EMA üstünde mi

Momentum:
- RSI
- MACD histogram
- fiyat değişim yüzdesi

Volatilite:
- ATR yüzdesi
- Bollinger genişliği
- mum boyu / ortalama mum boyu

Hacim:
- volume z-score
- MFI
- OBV değişimi

Likidite:
- spread
- order book depth
- slippage tahmini

Haber/Balina:
- haber sentiment skoru
- haber impact skoru
- whale notional skoru
- order book imbalance
```

### Planlanan modül

```text
src/crypto_paper_bot/ml/features.py
```

---

## 5. Scikit-Learn Katmanı — Klasik ML Modeli

### Görev

İlk ML aşamasında hızlı, ölçülebilir ve açıklanabilir modeller için Scikit-Learn kullanılacak.

### İlk modeller

```text
LogisticRegression
RandomForestClassifier
GradientBoostingClassifier
HistGradientBoostingClassifier
```

### Tahmin hedefleri

İlk aşamada model doğrudan “al/sat” demeyecek. Şunu tahmin edecek:

```text
Önümüzdeki N mum içinde fiyat, risk mesafesine göre anlamlı şekilde yukarı gider mi?
```

Örnek label:

```text
1 = sonraki 12 H1 mumda +1R veya daha fazla yükseldi
0 = yükselmedi veya önce -1R gördü
```

### Planlanan modül

```text
src/crypto_paper_bot/ml/sklearn_models.py
```

### Ana fonksiyonlar

```text
train_logistic_model()
train_random_forest_model()
train_gradient_boosting_model()
predict_probability()
save_sklearn_model()
load_sklearn_model()
```

---

## 6. PyTorch Katmanı — Gelişmiş Model Aşaması

### Görev

Yeterli veri toplandıktan sonra zaman serisi tabanlı daha gelişmiş model için PyTorch kullanılacak.

### Muhtemel modeller

```text
MLP baseline
1D CNN
GRU / LSTM
Transformer Encoder mini-model
```

### Ne zaman kullanılacak?

PyTorch hemen kullanılmayacak. Önce Scikit-Learn ile baseline başarı kanıtlanacak.

PyTorch şartları:

```text
- En az 3000+ temiz örnek
- Backtest metrikleri stabil
- Overfit kontrolü yapılmış
- Walk-forward test hazır
```

### Planlanan modül

```text
src/crypto_paper_bot/ml/torch_models.py
```

---

## 7. Scikit-Learn Metrics Katmanı — Başarı Ölçümü

### Görev

Modelin gerçekten işe yarayıp yaramadığını ölçer.

### Kullanılacak metrikler

```text
classification_report
accuracy_score
precision_score
recall_score
f1_score
roc_auc_score
confusion_matrix
log_loss
precision_recall_curve
```

### Trading odaklı ek metrikler

```text
net_pnl
profit_factor
max_drawdown
sharpe_ratio
win_rate
average_win / average_loss
fill_rate
slippage_adjusted_return
```

### Planlanan modül

```text
src/crypto_paper_bot/ml/evaluation.py
```

---

## 8. Modelin İşlem Özgüvenine Katılması

ML modeli tek başına işlem açtırmayacak. Sadece işlem özgüveni formülüne bir bileşen olarak girecek.

Planlanan formül:

```text
İşlem Özgüveni =
  İndikatör Skoru × dinamik_ağırlık
+ ML Tahmini × dinamik_ağırlık
+ Rejim Uyum Skoru × dinamik_ağırlık
+ Likidite Skoru × dinamik_ağırlık
+ Risk/Ödül Skoru × dinamik_ağırlık
+ Portföy Güvenliği Skoru × dinamik_ağırlık
+ Haber/Balina Skoru × dinamik_ağırlık
```

Ağırlıklar sabit kalmayacak. Veritabanındaki geçmiş başarıya göre güncellenecek.

İlk aşamada ağırlık güncellemesi kapalı olacak. Sadece kayıt yapılacak.

---

## 9. Eğitim Akışı

```text
1. Supabase/Postgres'ten OHLCV + haber + balina + işlem logları çek
2. Pandas DataFrame oluştur
3. Veriyi temizle
4. Feature engineering yap
5. NumPy array üret
6. Label oluştur
7. Train / validation / test ayır
8. Scikit-Learn baseline modellerini eğit
9. Metrikleri ölç
10. Walk-forward test yap
11. En iyi modeli kaydet
12. Paper-trade sırasında sadece tahmin skoru üret
13. Sonuçları tekrar veritabanına yaz
```

---

## 10. Planlanan Klasör Yapısı

```text
src/crypto_paper_bot/ml/
  __init__.py
  dataframe_cleaning.py
  features.py
  feature_arrays.py
  labels.py
  visual_diagnostics.py
  sklearn_models.py
  torch_models.py
  evaluation.py
  walk_forward.py
  model_registry.py
  training_pipeline.py
```

---

## 11. Önemli Politika

Bu aşama hemen uygulanmayacak.

Öncelik sırası:

```text
1. Mevcut UI sayfalarını tamamla
2. FastAPI endpointlerini sağlamlaştır
3. Supabase/Render/Vercel deploy uyumunu bitir
4. Paper-trade veri toplama stabil çalışsın
5. En az yeterli veri oluşsun
6. Sonra ML/Data Pipeline implementasyonuna geç
```

Bu belge sonraki aşama için mimari nottur.
