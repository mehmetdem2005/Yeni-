# Runtime Modes

Bu projede iki farklı çalışma modu vardır.

## 1. Termux-Light Modu

Amaç: Telefonda ağır derleme hatalarına girmeden uygulamanın çekirdeğini çalıştırmak.

Kurulum:

```bash
python -m pip install -e .
python -m crypto_paper_bot.app
```

Özellikler:

- Saf Python çekirdek
- SQLite
- Binance public veri çekme
- Hafif yerel ML modeli
- Sanal bakiye ve paper-trade paneli

Bilinçli olarak kaçınılanlar:

- pandas
- numpy
- scikit-learn
- pydantic
- psycopg

Bu paketler Termux'ta derleme sorunları çıkarabildiği için çekirdek bağımlılık yapılmaz.

## 2. Cloud / Desktop Full Mod

Amaç: Render, VPS, Google Cloud, Codespaces veya masaüstü ortamda tam araştırma sistemini çalıştırmak.

Kurulum:

```bash
python -m pip install -r requirements-cloud.txt
python -m pip install -e .
```

Özellikler:

- pandas/numpy/scikit-learn ile gelişmiş ML
- PostgreSQL/Supabase uyumlu katmanlar
- Daha gelişmiş backtest ve walk-forward testleri
- Render/Vercel/Supabase dağıtımına hazırlanmış yapı

## Neden ayrıldı?

Termux için çekirdeği hafifletirken cloud tarafındaki güçlü bağımlılıkları çekirdekten çıkardık. Bu bilinçli bir ayrımdır. Termux bozulmasın diye ağır paketler opsiyonel tutulur; cloud tarafında `requirements-cloud.txt` ile geri yüklenir.
