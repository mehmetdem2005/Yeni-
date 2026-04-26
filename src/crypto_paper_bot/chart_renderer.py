from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChartTheme:
    background: str = "#020617"
    grid: str = "#1f2937"
    text: str = "#94a3b8"
    line: str = "#60a5fa"
    line_secondary: str = "#fbbf24"
    positive: str = "#22c55e"
    negative: str = "#ef4444"
    neutral: str = "#64748b"
    warning: str = "#f59e0b"


DEFAULT_THEME = ChartTheme()


def _value(row: Any, key: str) -> float:
    if isinstance(row, dict):
        return float(row[key])
    return float(getattr(row, key))


def _safe_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fmt(value: float, digits: int = 2) -> str:
    if abs(value) >= 1000:
        return f"{value:,.0f}"
    if abs(value) >= 10:
        return f"{value:.2f}"
    return f"{value:.{digits}f}"


def _normalize_points(values: list[float], width: int, height: int, pad: int) -> list[tuple[float, float]]:
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi == lo:
        hi = lo + 1.0
    usable_w = max(width - pad * 2, 1)
    usable_h = max(height - pad * 2, 1)
    points: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        x = pad + (index * usable_w / max(len(values) - 1, 1))
        y = pad + ((hi - value) / (hi - lo)) * usable_h
        points.append((x, y))
    return points


def _polyline(points: list[tuple[float, float]], color: str, width: float = 2.5) -> str:
    if not points:
        return ""
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f"<polyline points='{joined}' fill='none' stroke='{color}' stroke-width='{width}' stroke-linecap='round' stroke-linejoin='round'/>"


def _base_svg(width: int, height: int, body: str, title: str = "", subtitle: str = "", theme: ChartTheme = DEFAULT_THEME) -> str:
    title_svg = ""
    if title:
        title_svg += f"<text x='14' y='22' fill='{theme.text}' font-size='13' font-weight='700'>{_safe_text(title)}</text>"
    if subtitle:
        title_svg += f"<text x='14' y='40' fill='{theme.text}' font-size='11'>{_safe_text(subtitle)}</text>"
    return (
        f"<svg viewBox='0 0 {width} {height}' class='svg-chart' role='img' "
        f"style='width:100%;height:auto;background:{theme.background};border-radius:14px'>"
        f"<rect x='0' y='0' width='{width}' height='{height}' rx='14' fill='{theme.background}'/>"
        f"{title_svg}{body}</svg>"
    )


def line_chart(
    values: list[float],
    title: str = "Çizgi Grafik",
    subtitle: str = "",
    width: int = 760,
    height: int = 220,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    if len(values) < 2:
        return "<div class='empty'>Grafik için yeterli veri yok.</div>"
    pad = 44
    points = _normalize_points(values, width, height, pad)
    lo = min(values)
    hi = max(values)
    body = ""
    for i in range(1, 4):
        y = pad + i * ((height - pad * 2) / 4)
        body += f"<line x1='{pad}' y1='{y:.1f}' x2='{width-pad}' y2='{y:.1f}' stroke='{theme.grid}' stroke-width='1'/>"
    body += _polyline(points, theme.line, 3.0)
    body += f"<text x='{pad}' y='{height-12}' fill='{theme.text}' font-size='11'>Min {_fmt(lo)}</text>"
    body += f"<text x='{width-pad-110}' y='{height-12}' fill='{theme.text}' font-size='11'>Max {_fmt(hi)}</text>"
    return _base_svg(width, height, body, title, subtitle, theme)


def dual_line_chart(
    primary: list[float],
    secondary: list[float],
    title: str = "Fiyat + Ortalama",
    primary_label: str = "Fiyat",
    secondary_label: str = "EMA",
    width: int = 760,
    height: int = 240,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    if len(primary) < 2 or len(secondary) < 2:
        return "<div class='empty'>Grafik için yeterli veri yok.</div>"
    length = min(len(primary), len(secondary))
    primary = primary[-length:]
    secondary = secondary[-length:]
    all_values = primary + secondary
    pad = 46
    lo = min(all_values)
    hi = max(all_values)
    if hi == lo:
        hi = lo + 1.0

    def project(values: list[float]) -> list[tuple[float, float]]:
        points: list[tuple[float, float]] = []
        usable_w = width - pad * 2
        usable_h = height - pad * 2
        for index, value in enumerate(values):
            x = pad + index * usable_w / max(len(values) - 1, 1)
            y = pad + ((hi - value) / (hi - lo)) * usable_h
            points.append((x, y))
        return points

    body = ""
    for i in range(1, 4):
        y = pad + i * ((height - pad * 2) / 4)
        body += f"<line x1='{pad}' y1='{y:.1f}' x2='{width-pad}' y2='{y:.1f}' stroke='{theme.grid}' stroke-width='1'/>"
    body += _polyline(project(primary), theme.line, 3.0)
    body += _polyline(project(secondary), theme.line_secondary, 2.4)
    body += f"<circle cx='{width-160}' cy='20' r='5' fill='{theme.line}'/><text x='{width-150}' y='24' fill='{theme.text}' font-size='11'>{_safe_text(primary_label)}</text>"
    body += f"<circle cx='{width-90}' cy='20' r='5' fill='{theme.line_secondary}'/><text x='{width-80}' y='24' fill='{theme.text}' font-size='11'>{_safe_text(secondary_label)}</text>"
    body += f"<text x='{pad}' y='{height-12}' fill='{theme.text}' font-size='11'>Min {_fmt(lo)}</text>"
    body += f"<text x='{width-pad-110}' y='{height-12}' fill='{theme.text}' font-size='11'>Max {_fmt(hi)}</text>"
    return _base_svg(width, height, body, title, "Fiyat ve hareketli ortalama birlikte gösterilir.", theme)


def candle_chart(
    candles: list[Any],
    title: str = "Mum Grafiği",
    width: int = 760,
    height: int = 300,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    if len(candles) < 2:
        return "<div class='empty'>Mum grafiği için yeterli veri yok.</div>"
    candles = candles[-80:]
    highs = [_value(c, "high") for c in candles]
    lows = [_value(c, "low") for c in candles]
    lo = min(lows)
    hi = max(highs)
    if hi == lo:
        hi = lo + 1.0
    pad = 46
    usable_w = width - pad * 2
    usable_h = height - pad * 2
    candle_w = max(3.0, usable_w / max(len(candles), 1) * 0.55)

    def y_price(price: float) -> float:
        return pad + ((hi - price) / (hi - lo)) * usable_h

    body = ""
    for i in range(1, 4):
        y = pad + i * (usable_h / 4)
        body += f"<line x1='{pad}' y1='{y:.1f}' x2='{width-pad}' y2='{y:.1f}' stroke='{theme.grid}' stroke-width='1'/>"
    for index, candle in enumerate(candles):
        open_price = _value(candle, "open")
        close_price = _value(candle, "close")
        high = _value(candle, "high")
        low = _value(candle, "low")
        x = pad + index * usable_w / max(len(candles) - 1, 1)
        color = theme.positive if close_price >= open_price else theme.negative
        y_high = y_price(high)
        y_low = y_price(low)
        y_open = y_price(open_price)
        y_close = y_price(close_price)
        rect_y = min(y_open, y_close)
        rect_h = max(abs(y_close - y_open), 2.0)
        body += f"<line x1='{x:.1f}' y1='{y_high:.1f}' x2='{x:.1f}' y2='{y_low:.1f}' stroke='{color}' stroke-width='1.2'/>"
        body += f"<rect x='{x-candle_w/2:.1f}' y='{rect_y:.1f}' width='{candle_w:.1f}' height='{rect_h:.1f}' rx='1.5' fill='{color}' opacity='0.9'/>"
    body += f"<text x='{pad}' y='{height-12}' fill='{theme.text}' font-size='11'>Dip {_fmt(lo)}</text>"
    body += f"<text x='{width-pad-110}' y='{height-12}' fill='{theme.text}' font-size='11'>Tepe {_fmt(hi)}</text>"
    return _base_svg(width, height, body, title, "Yeşil mum yükseliş, kırmızı mum düşüş anlamına gelir.", theme)


def bar_chart(
    values: list[float],
    title: str = "Bar Grafik",
    subtitle: str = "",
    width: int = 760,
    height: int = 220,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    if len(values) < 2:
        return "<div class='empty'>Bar grafiği için yeterli veri yok.</div>"
    values = values[-120:]
    pad = 44
    max_value = max(values) if values else 1.0
    if max_value <= 0:
        max_value = 1.0
    usable_w = width - pad * 2
    usable_h = height - pad * 2
    bar_w = max(2.0, usable_w / len(values) * 0.65)
    body = ""
    for i, value in enumerate(values):
        x = pad + i * usable_w / max(len(values) - 1, 1)
        bar_h = (max(value, 0.0) / max_value) * usable_h
        y = height - pad - bar_h
        body += f"<rect x='{x-bar_w/2:.1f}' y='{y:.1f}' width='{bar_w:.1f}' height='{bar_h:.1f}' rx='1.5' fill='{theme.line}' opacity='0.75'/>"
    body += f"<text x='{pad}' y='{height-12}' fill='{theme.text}' font-size='11'>Maksimum {_fmt(max_value)}</text>"
    return _base_svg(width, height, body, title, subtitle, theme)


def rsi_chart(
    rsi_values: list[float],
    title: str = "RSI Grafiği",
    width: int = 760,
    height: int = 220,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    clean = [max(0.0, min(100.0, float(v))) for v in rsi_values if v is not None]
    if len(clean) < 2:
        return "<div class='empty'>RSI grafiği için yeterli veri yok.</div>"
    clean = clean[-120:]
    pad = 44
    usable_w = width - pad * 2
    usable_h = height - pad * 2

    def project(value: float, index: int) -> tuple[float, float]:
        x = pad + index * usable_w / max(len(clean) - 1, 1)
        y = pad + ((100.0 - value) / 100.0) * usable_h
        return x, y

    points = [project(value, index) for index, value in enumerate(clean)]
    y70 = pad + ((100.0 - 70.0) / 100.0) * usable_h
    y30 = pad + ((100.0 - 30.0) / 100.0) * usable_h
    body = f"<line x1='{pad}' y1='{y70:.1f}' x2='{width-pad}' y2='{y70:.1f}' stroke='{theme.warning}' stroke-width='1.4' stroke-dasharray='4 4'/>"
    body += f"<line x1='{pad}' y1='{y30:.1f}' x2='{width-pad}' y2='{y30:.1f}' stroke='{theme.warning}' stroke-width='1.4' stroke-dasharray='4 4'/>"
    body += _polyline(points, theme.line, 3.0)
    body += f"<text x='{pad}' y='{y70-4:.1f}' fill='{theme.text}' font-size='11'>70 aşırı ısınma</text>"
    body += f"<text x='{pad}' y='{y30+14:.1f}' fill='{theme.text}' font-size='11'>30 zayıflık</text>"
    body += f"<text x='{width-pad-100}' y='{height-12}' fill='{theme.text}' font-size='11'>Son RSI {_fmt(clean[-1])}</text>"
    return _base_svg(width, height, body, title, "Momentumun dengeli mi, aşırı mı olduğunu gösterir.", theme)


def atr_chart(
    atr_values: list[float],
    title: str = "ATR / Oynaklık Grafiği",
    width: int = 760,
    height: int = 220,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    clean = [float(v) for v in atr_values if v is not None and float(v) >= 0]
    return line_chart(clean[-120:], title, "ATR yükselirse stop mesafesi ve risk büyür.", width, height, theme)


def equity_chart(
    equity_points: list[dict[str, Any]],
    title: str = "Sanal Para Grafiği",
    width: int = 760,
    height: int = 220,
    theme: ChartTheme = DEFAULT_THEME,
) -> str:
    values = [float(point["equity"]) for point in equity_points if "equity" in point]
    return line_chart(values, title, "Sanal hesabın zaman içindeki toplam değerini gösterir.", width, height, theme)


def confidence_gauge(value: float | None, title: str = "Özgüven", theme: ChartTheme = DEFAULT_THEME) -> str:
    if value is None:
        value = 0.0
    value = max(0.0, min(1.0, float(value)))
    width = 320
    height = 90
    fill_w = 260 * value
    color = theme.positive if value >= 0.70 else theme.warning if value >= 0.50 else theme.negative
    percent = f"%{value * 100:.1f}"
    body = f"<text x='18' y='24' fill='{theme.text}' font-size='13' font-weight='700'>{_safe_text(title)}</text>"
    body += f"<rect x='18' y='42' width='260' height='18' rx='9' fill='{theme.grid}'/>"
    body += f"<rect x='18' y='42' width='{fill_w:.1f}' height='18' rx='9' fill='{color}'/>"
    body += f"<text x='288' y='57' fill='{theme.text}' font-size='13' font-weight='700'>{percent}</text>"
    return _base_svg(width, height, body, "", "", theme)


def candles_to_ohlc_lists(candles: list[Any]) -> dict[str, list[float]]:
    return {
        "open": [_value(c, "open") for c in candles],
        "high": [_value(c, "high") for c in candles],
        "low": [_value(c, "low") for c in candles],
        "close": [_value(c, "close") for c in candles],
        "volume": [_value(c, "volume") for c in candles],
    }
