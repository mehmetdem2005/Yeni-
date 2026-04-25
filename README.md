# Crypto Spot Bot — Paper Trade Core v1.0

Bu repo, **canlı para için değil**, paper-trade ve backtest aşaması için tasarlanmış kripto spot bot iskeletidir.

## Durum

- Spot only
- Long only
- Kaldıraç yok
- Short yok
- Canlı öğrenme kapalı
- Withdrawal yetkisi kullanılmaz

## Çekirdek Mantık

- W1: ana rejim kapısı
- D1: günlük yön kapısı
- H1: giriş sinyali
- ATR puana girmez; sadece SL, TP ve pozisyon büyüklüğü için kullanılır.

## Hızlı Başlangıç

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp configs/config.example.yaml configs/config.local.yaml
python -m crypto_paper_bot.cli validate-config configs/config.local.yaml
```

Demo simülasyon:

```bash
python -m crypto_paper_bot.cli demo
```

## Önemli Uyarı

Bu yazılım finansal tavsiye değildir. Gerçek emir göndermek için hazır değildir. Önce walk-forward backtest ve en az 60 gün paper trade yapılmalıdır.
