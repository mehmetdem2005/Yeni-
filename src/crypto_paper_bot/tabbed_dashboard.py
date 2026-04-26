from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from crypto_paper_bot.chart_renderer import confidence_gauge, equity_chart
from crypto_paper_bot.log_channels import LogChannel, LogRecord, channel_title, filter_logs


TABS = [
    "ana",
    "piyasa",
    "indikatorler",
    "aileler",
    "yapay_zeka",
    "risk",
    "loglar",
    "haberler",
]

TAB_TITLES = {
    "ana": "Ana Panel",
    "piyasa": "Piyasa Grafikleri",
    "indikatorler": "İndikatörler",
    "aileler": "Aileler",
    "yapay_zeka": "Yapay Zekâ",
    "risk": "Risk Yönetimi",
    "loglar": "Loglar",
    "haberler": "Haber Akışı",
}


@dataclass(frozen=True)
class DashboardContext:
    active_tab: str
    system_confidence: dict[str, Any] | None
    wallet: dict[str, Any]
    trade_stats: dict[str, Any]
    equity_points: list[dict[str, Any]]
    analyses: list[dict[str, Any]]
    indicator_snapshots: list[dict[str, Any]]
    family_snapshots: list[dict[str, Any]]
    model_state: dict[str, Any] | None
    risk_plans: list[dict[str, Any]]
    logs: list[LogRecord]
    news_items: list[dict[str, Any]]
    background: dict[str, Any]
    message: str = ""


def esc(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def money(value: Any) -> str:
    try:
        return f"{float(value):,.2f} USDT"
    except Exception:
        return "-"


def pct(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"%{float(value) * 100:.1f}"
    except Exception:
        return "-"


def num(value: Any, digits: int = 3) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return esc(value)


def tab_url(tab: str) -> str:
    return f"/?tab={tab}"


def nav(active_tab: str) -> str:
    links = []
    for tab in TABS:
        cls = "active" if tab == active_tab else ""
        links.append(f"<a class='{cls}' href='{tab_url(tab)}'>{esc(TAB_TITLES[tab])}</a>")
    return "<nav class='tabs'>" + "".join(links) + "</nav>"


def metric(label: str, value: str, hint: str = "") -> str:
    return f"""
    <div class='metric'>
      <b>{esc(label)}</b>
      <span>{value}</span>
      {f"<small>{esc(hint)}</small>" if hint else ""}
    </div>
    """


def status_badge(text: str, kind: str = "neutral") -> str:
    return f"<span class='badge {kind}'>{esc(text)}</span>"


def main_tab(ctx: DashboardContext) -> str:
    wallet = ctx.wallet or {}
    stats = ctx.trade_stats or {}
    start = float(wallet.get("starting_balance") or 10000.0)
    last_equity = ctx.equity_points[-1]["equity"] if ctx.equity_points else wallet.get("cash", start)
    pnl = float(last_equity) - start
    pnl_class = "good-text" if pnl >= 0 else "bad-text"
    sys_conf = (ctx.system_confidence or {}).get("system_confidence")
    running = bool(ctx.background.get("running"))

    cards = "".join(
        [
            metric("Toplam Sanal Para", money(last_equity), "Sanal hesap değeri."),
            metric("Nakit", money(wallet.get("cash", 0)), "İşlemde olmayan sanal para."),
            metric("Toplam Kâr/Zarar", f"<span class='{pnl_class}'>{money(pnl)}</span>", "Başlangıca göre fark."),
            metric("Başarı Oranı", pct(stats.get("win_rate", 0)), "Kapanan işlemlerde kazanma oranı."),
            metric("Açık İşlem", str(stats.get("open_count", 0)), "Şu anda kapanmamış sanal işlem."),
            metric("Sistem Durumu", "Çalışıyor" if running else "Durduruldu", "Otomatik döngü durumu."),
        ]
    )
    return f"""
    <section class='card hero-card'>
      <div>
        <h2>Ana Panel</h2>
        <p class='muted'>Sistem gerçek veriyi toplar, modeli eğitir, risk motoruyla sanal işlem arar.</p>
      </div>
      <div class='top-confidence'>{confidence_gauge(sys_conf, 'Sistem Özgüveni')}</div>
    </section>
    <section class='card'>
      <h2>Sanal Para Durumu</h2>
      <div class='grid'>{cards}</div>
    </section>
    <section class='card'>
      <h2>Kâr Grafiği</h2>
      {equity_chart(ctx.equity_points)}
    </section>
    <section class='card'>
      <h2>Kontrol</h2>
      <form class='actions' method='post'>
        <button name='action' value='cycle'>Sistemi Bir Tur Çalıştır</button>
        <button name='action' value='start'>Otomatik Başlat</button>
        <button class='danger' name='action' value='stop'>Durdur</button>
        <button class='secondary' name='action' value='collect'>Sadece Veri Topla</button>
        <button class='secondary' name='action' value='train'>Sadece Eğit</button>
        <button class='danger' name='action' value='reset'>Sanal Hesabı Sıfırla</button>
      </form>
    </section>
    """


def market_tab(ctx: DashboardContext) -> str:
    if not ctx.analyses:
        return "<section class='card'><h2>Piyasa Grafikleri</h2><div class='empty'>Henüz analiz yok. Önce ana panelden bir tur çalıştır.</div></section>"
    cards = []
    for item in ctx.analyses:
        decision = str(item.get("decision") or "İZLE")
        kind = "good" if "ALIM" in decision or "CANDIDATE" in decision else "neutral"
        cards.append(
            f"""
            <div class='coin-card'>
              <div class='coin-head'><h3>{esc(item.get('symbol'))}</h3>{status_badge(decision, kind)}</div>
              <p class='muted'>{esc(item.get('explanation') or 'Sistem bu coin için son durumu analiz etti.')}</p>
              <div class='mini-grid'>
                <div><b>Piyasanın alış fiyatı</b><span>{num(item.get('bid'), 4)}</span></div>
                <div><b>Piyasanın satış fiyatı</b><span>{num(item.get('ask'), 4)}</span></div>
                <div><b>İndikatör skoru</b><span>{pct(item.get('score'))}</span></div>
                <div><b>Yapay zekâ tahmini</b><span>{pct(item.get('ml_probability'))}</span></div>
                <div><b>Büyük yön</b><span>{'Olumlu' if item.get('weekly_ok') else 'Zayıf'}</span></div>
                <div><b>Günlük yön</b><span>{'Olumlu' if item.get('daily_ok') else 'Zayıf'}</span></div>
              </div>
            </div>
            """
        )
    return f"<section class='card'><h2>Piyasa Grafikleri</h2><p class='muted'>Bu sekmede mum grafikleri ve fiyat/EMA grafikleri bağlanacak. Şimdilik coin karar kartları gösteriliyor.</p><div class='coins'>{''.join(cards)}</div></section>"


def indicators_tab(ctx: DashboardContext) -> str:
    if not ctx.indicator_snapshots:
        return "<section class='card'><h2>İndikatörler</h2><div class='empty'>Henüz indikatör kaydı yok.</div></section>"
    cards = []
    for item in ctx.indicator_snapshots:
        cards.append(
            f"""
            <div class='coin-card'>
              <h3>{esc(item.get('symbol'))}</h3>
              <div class='mini-grid'>
                <div><b>EMA Sinyali</b><span>{pct(item.get('ema_signal'))}</span></div>
                <div><b>RSI</b><span>{num(item.get('rsi_value'), 2)}</span></div>
                <div><b>ATR</b><span>{num(item.get('atr_value'), 4)}</span></div>
                <div><b>Hacim Oranı</b><span>{num(item.get('volume_ratio'), 2)}</span></div>
                <div><b>İndikatör Skoru</b><span>{pct(item.get('indicator_score'))}</span></div>
              </div>
              <p>{esc(item.get('decision_comment') or '')}</p>
            </div>
            """
        )
    return f"<section class='card'><h2>İndikatörler</h2><p class='muted'>Her indikatörün değeri, yorumu ve karara etkisi burada gösterilir.</p><div class='coins'>{''.join(cards)}</div></section>"


def families_tab(ctx: DashboardContext) -> str:
    if not ctx.family_snapshots:
        return "<section class='card'><h2>Aileler</h2><div class='empty'>Henüz aile skoru yok.</div></section>"
    blocks = []
    for snapshot in ctx.family_snapshots:
        family_cards = []
        families = snapshot.get("families", {})
        for _, family in families.items():
            family_cards.append(
                f"""
                <div class='metric'>
                  <b>{esc(family.get('title'))}</b>
                  <span>{pct(family.get('score'))}</span>
                  <small>{esc(family.get('comment'))}</small>
                </div>
                """
            )
        blocks.append(
            f"<div class='coin-card'><h3>{esc(snapshot.get('symbol'))}</h3><p>{esc(snapshot.get('summary'))}</p><div class='grid'>{''.join(family_cards)}</div></div>"
        )
    return f"<section class='card'><h2>Aileler</h2><p class='muted'>İndikatörler ailelere ayrılır. Bu ekran hangi tarafın kararı güçlendirdiğini gösterir.</p><div class='stack'>{''.join(blocks)}</div></section>"


def ai_tab(ctx: DashboardContext) -> str:
    model = ctx.model_state or {}
    metrics = model.get("metrics", {}) if isinstance(model, dict) else {}
    weights = model.get("weights", {}) if isinstance(model, dict) else {}
    weight_rows = "".join(
        f"<tr><td>{esc(k)}</td><td>{num(v, 4)}</td><td>{weight_explanation(k, float(v))}</td></tr>"
        for k, v in weights.items()
    )
    if not weight_rows:
        weight_rows = "<tr><td colspan='3'>Henüz model ağırlığı yok. Önce eğitim çalıştır.</td></tr>"
    cards = "".join(
        [
            metric("Eğitim Örneği", str(model.get("trained_samples", 0)), "Modelin gördüğü örnek sayısı."),
            metric("Model Doğruluğu", pct(metrics.get("accuracy")), "Geçmiş örneklerdeki yaklaşık doğruluk."),
            metric("Olumlu Örnek Oranı", pct(metrics.get("positive_rate")), "Veride olumlu kabul edilen örneklerin oranı."),
            metric("Son Eğitim", esc(model.get("updated_at") or "-"), "Modelin son güncellenme zamanı."),
        ]
    )
    return f"""
    <section class='card'>
      <h2>Yapay Zekâ</h2>
      <p class='muted'>Bu model işlem açmaz; geçmiş örneklerden olasılık üretir ve karar motoruna bir bileşen olarak katılır.</p>
      <div class='grid'>{cards}</div>
    </section>
    <section class='card'>
      <h2>Model Neye Dikkat Ediyor?</h2>
      <table><thead><tr><th>Özellik</th><th>Ağırlık</th><th>Yorum</th></tr></thead><tbody>{weight_rows}</tbody></table>
    </section>
    """


def weight_explanation(key: str, value: float) -> str:
    direction = "olumlu etkiliyor" if value > 0 else "olumsuz etkiliyor" if value < 0 else "nötr"
    names = {
        "bias": "Genel eğilim",
        "ret_1": "Son mum hareketi",
        "ret_3": "Kısa vadeli momentum",
        "ret_6": "Orta-kısa momentum",
        "range_pct": "Mum oynaklığı",
        "volume_ratio": "Hacim artışı",
        "ema_distance": "Trend farkı",
    }
    return f"{names.get(key, key)} modeli {direction}."


def risk_tab(ctx: DashboardContext) -> str:
    if not ctx.risk_plans:
        return "<section class='card'><h2>Risk Yönetimi</h2><div class='empty'>Henüz risk planı yok.</div></section>"
    rows = []
    for plan in ctx.risk_plans:
        rows.append(
            f"""
            <tr>
              <td>{esc(plan.get('symbol'))}</td>
              <td>{'Uygun' if plan.get('ok') else 'Reddedildi'}</td>
              <td>{money(plan.get('final_position_notional'))}</td>
              <td>{num(plan.get('stop_loss'), 4)}</td>
              <td>{num(plan.get('take_profit'), 4)}</td>
              <td>{num(plan.get('reward_risk'), 2)}</td>
            </tr>
            <tr><td colspan='6' class='explain-cell'>{esc(plan.get('explanation'))}</td></tr>
            """
        )
    return f"<section class='card'><h2>Risk Yönetimi</h2><p class='muted'>Akıllı miktar, stop-loss ve take-profit burada açıklanır.</p><table><thead><tr><th>Coin</th><th>Durum</th><th>Miktar</th><th>Zarar Kes</th><th>Kâr Al</th><th>R/R</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>"


def logs_tab(ctx: DashboardContext) -> str:
    channel_buttons = "".join(
        f"<a class='log-chip' href='/?tab=loglar&channel={channel.value}'>{esc(channel_title(channel))}</a>"
        for channel in LogChannel
    )
    sections = []
    for channel in LogChannel:
        records = filter_logs(ctx.logs, channel)[:30]
        rows = "".join(
            f"<tr><td>{esc(r.created_at)}</td><td>{esc(r.level.value)}</td><td>{esc(r.message)}</td><td>{esc(r.user_explanation)}</td></tr>"
            for r in records
        )
        if not rows:
            rows = "<tr><td colspan='4'>Bu kanalda henüz log yok.</td></tr>"
        sections.append(
            f"<section class='log-section'><h3>{esc(channel_title(channel))}</h3><table><thead><tr><th>Zaman</th><th>Seviye</th><th>Kayıt</th><th>Açıklama</th></tr></thead><tbody>{rows}</tbody></table></section>"
        )
    return f"<section class='card'><h2>Loglar</h2><p class='muted'>Loglar ayrı kanallara bölünür. Böylece indikatör, aile, risk ve hata kayıtları karışmaz.</p><div class='log-chips'>{channel_buttons}</div>{''.join(sections)}</section>"


def news_tab(ctx: DashboardContext) -> str:
    if not ctx.news_items:
        return "<section class='card'><h2>Haber Akışı</h2><div class='empty'>Henüz haber çekilmedi. Haberler ilk aşamada işlem kararını doğrudan değiştirmez.</div></section>"
    cards = []
    for item in ctx.news_items[:40]:
        sentiment = item.get("sentiment", "Nötr")
        kind = "good" if sentiment == "Pozitif" else "bad" if sentiment == "Negatif" else "neutral"
        cards.append(
            f"""
            <article class='news-card'>
              <div>{status_badge(sentiment, kind)} <small>{esc(item.get('source'))} · {esc(item.get('published_at'))}</small></div>
              <h3><a href='{esc(item.get('link'))}' target='_blank' rel='noreferrer'>{esc(item.get('title'))}</a></h3>
              <p>{esc(item.get('summary'))}</p>
              <small>İlgili coinler: {esc(', '.join(item.get('related_symbols') or []) or '-')}</small>
            </article>
            """
        )
    return f"<section class='card'><h2>Haber Akışı</h2><p class='muted'>Haberler bilgilendirme amaçlıdır. Sonraki sürümde haber risk filtresi eklenecek.</p><div class='news-list'>{''.join(cards)}</div></section>"


def content_for_tab(ctx: DashboardContext) -> str:
    active = ctx.active_tab if ctx.active_tab in TABS else "ana"
    if active == "ana":
        return main_tab(ctx)
    if active == "piyasa":
        return market_tab(ctx)
    if active == "indikatorler":
        return indicators_tab(ctx)
    if active == "aileler":
        return families_tab(ctx)
    if active == "yapay_zeka":
        return ai_tab(ctx)
    if active == "risk":
        return risk_tab(ctx)
    if active == "loglar":
        return logs_tab(ctx)
    if active == "haberler":
        return news_tab(ctx)
    return main_tab(ctx)


def render_dashboard(ctx: DashboardContext) -> str:
    active_tab = ctx.active_tab if ctx.active_tab in TABS else "ana"
    sys_conf = (ctx.system_confidence or {}).get("system_confidence")
    message = f"<div class='message'>{esc(ctx.message)}</div>" if ctx.message else ""
    return f"""<!doctype html>
<html lang='tr'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width,initial-scale=1'>
  <meta http-equiv='refresh' content='30'>
  <title>Kripto Kontrol Merkezi</title>
  <style>{dashboard_css()}</style>
</head>
<body>
  <header class='topbar'>
    <div><h1>Kripto Sanal Alım-Satım Kontrol Merkezi</h1><p>Gerçek veri · Sanal para · İndikatörler · Yapay zekâ · Risk motoru</p></div>
    <div class='system-confidence'>{confidence_gauge(sys_conf, 'Sistem Özgüveni')}</div>
  </header>
  <main class='wrap'>
    {nav(active_tab)}
    {message}
    {content_for_tab(ctx)}
  </main>
</body>
</html>"""


def dashboard_css() -> str:
    return """
    *{box-sizing:border-box} body{margin:0;background:#08111f;color:#e5e7eb;font-family:Arial,sans-serif}
    .topbar{position:sticky;top:0;z-index:10;background:#0f172a;border-bottom:1px solid #334155;padding:12px 18px;display:flex;gap:16px;justify-content:space-between;align-items:center}
    .topbar h1{margin:0;font-size:22px}.topbar p{margin:4px 0 0;color:#94a3b8}.system-confidence{width:320px;max-width:42vw}
    .wrap{max-width:1220px;margin:0 auto;padding:16px}.tabs{display:flex;gap:8px;overflow:auto;padding:8px 0 14px}.tabs a{white-space:nowrap;text-decoration:none;color:#cbd5e1;background:#111827;border:1px solid #334155;border-radius:999px;padding:10px 13px;font-weight:800}.tabs a.active{background:#2563eb;color:white;border-color:#60a5fa}
    .card{background:#111827;border:1px solid #334155;border-radius:22px;padding:18px;margin:14px 0;box-shadow:0 14px 34px rgba(0,0,0,.28)}.hero-card{display:flex;justify-content:space-between;gap:16px;align-items:center}.top-confidence{width:320px;max-width:100%}
    h2{margin:0 0 12px;color:#93c5fd}h3{margin:0 0 8px}.muted{color:#a7b4c8}.message{background:#172554;border:1px solid #2563eb;border-radius:14px;padding:12px;margin:10px 0}.empty{background:#020617;border-radius:14px;padding:16px;color:#94a3b8}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px}.metric{background:#020617;border:1px solid #1f2937;border-radius:16px;padding:14px}.metric b{display:block;color:#94a3b8;font-size:13px;margin-bottom:8px}.metric span{font-size:21px;font-weight:900}.metric small{display:block;margin-top:8px;color:#94a3b8}.good-text{color:#86efac}.bad-text{color:#fca5a5}
    .actions{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:10px}button{width:100%;padding:14px;border:0;border-radius:14px;background:#2563eb;color:white;font-weight:900}.secondary{background:#334155}.danger{background:#dc2626}
    .coins{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}.coin-card{background:#020617;border:1px solid #263244;border-radius:18px;padding:14px}.coin-head{display:flex;justify-content:space-between;align-items:center;gap:8px}.mini-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.mini-grid div{background:#0f172a;border-radius:12px;padding:10px}.mini-grid b{display:block;color:#94a3b8;font-size:12px}.mini-grid span{font-weight:900}.badge{display:inline-block;border-radius:999px;padding:6px 9px;font-size:12px;font-weight:900}.good{background:#065f46;color:#86efac}.bad{background:#7f1d1d;color:#fecaca}.neutral{background:#334155;color:#e5e7eb}
    table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid #263244;padding:10px;font-size:13px;vertical-align:top}th{color:#93c5fd}.explain-cell{color:#cbd5e1;background:#020617}.stack{display:grid;gap:12px}.log-chips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 16px}.log-chip{color:#e5e7eb;text-decoration:none;background:#020617;border:1px solid #334155;border-radius:999px;padding:8px 10px;font-size:12px}.log-section{margin-top:16px}.news-list{display:grid;gap:12px}.news-card{background:#020617;border:1px solid #263244;border-radius:18px;padding:14px}.news-card a{color:#93c5fd;text-decoration:none}.news-card p{color:#cbd5e1}.svg-chart{max-width:100%}
    @media(max-width:720px){.topbar{display:block}.system-confidence{width:100%;max-width:100%;margin-top:10px}.hero-card{display:block}.mini-grid{grid-template-columns:1fr}.tabs a{font-size:13px;padding:9px 11px}}
    """
