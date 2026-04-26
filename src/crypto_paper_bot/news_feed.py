from __future__ import annotations

import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from crypto_paper_bot.log_channels import LogChannel, LogLevel, LogRecord, make_log
from crypto_paper_bot.rate_limiter import RateLimiter


DEFAULT_NEWS_SOURCES = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
]

POSITIVE_WORDS = {
    "surge",
    "rally",
    "gain",
    "gains",
    "jump",
    "jumps",
    "bullish",
    "record",
    "approve",
    "approval",
    "adoption",
    "growth",
    "breakout",
    "positive",
    "up",
    "yükseliş",
    "artış",
    "olumlu",
    "onay",
    "rekor",
}

NEGATIVE_WORDS = {
    "drop",
    "drops",
    "fall",
    "falls",
    "crash",
    "bearish",
    "hack",
    "lawsuit",
    "ban",
    "probe",
    "risk",
    "selloff",
    "negative",
    "down",
    "düşüş",
    "çöküş",
    "hack",
    "yasak",
    "dava",
    "risk",
    "olumsuz",
}

COIN_KEYWORDS = {
    "BTC/USDT": ["btc", "bitcoin"],
    "ETH/USDT": ["eth", "ethereum"],
    "BNB/USDT": ["bnb", "binance"],
    "SOL/USDT": ["sol", "solana"],
}


@dataclass(frozen=True)
class NewsSource:
    name: str
    url: str
    enabled: bool = True


@dataclass(frozen=True)
class NewsItem:
    source: str
    title: str
    link: str
    published_at: str
    summary: str
    sentiment: str
    sentiment_score: float
    related_symbols: list[str]


@dataclass(frozen=True)
class NewsFeedResult:
    items: list[NewsItem]
    source_count: int
    errors: list[str]
    logs: list[LogRecord] = field(default_factory=list)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def safe_text(value: str | None) -> str:
    return strip_html(value or "")


def parse_rss_datetime(value: str | None) -> str:
    if not value:
        return utc_now()
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat(timespec="seconds")
    except Exception:
        return utc_now()


def classify_sentiment(title: str, summary: str = "") -> tuple[str, float]:
    text = f"{title} {summary}".lower()
    words = set(re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", text))
    positive = len(words & POSITIVE_WORDS)
    negative = len(words & NEGATIVE_WORDS)
    raw = positive - negative
    if raw > 0:
        return "Pozitif", min(1.0, 0.55 + raw * 0.12)
    if raw < 0:
        return "Negatif", max(0.0, 0.45 + raw * 0.12)
    return "Nötr", 0.50


def related_symbols(title: str, summary: str = "") -> list[str]:
    text = f"{title} {summary}".lower()
    found: list[str] = []
    for symbol, keywords in COIN_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            found.append(symbol)
    return found


def fetch_text(url: str, timeout: int = 15) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "crypto-paper-bot/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_rss(source: NewsSource, xml_text: str, max_items: int = 20) -> list[NewsItem]:
    root = ET.fromstring(xml_text)
    items: list[NewsItem] = []

    for item in root.findall(".//item")[:max_items]:
        title = safe_text(item.findtext("title"))
        link = safe_text(item.findtext("link"))
        summary = safe_text(item.findtext("description"))
        published = parse_rss_datetime(item.findtext("pubDate"))
        sentiment, score = classify_sentiment(title, summary)
        items.append(
            NewsItem(
                source=source.name,
                title=title,
                link=link,
                published_at=published,
                summary=summary[:240],
                sentiment=sentiment,
                sentiment_score=score,
                related_symbols=related_symbols(title, summary),
            )
        )

    # Atom fallback.
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns)[:max_items]:
            title = safe_text(entry.findtext("atom:title", default="", namespaces=ns))
            link_node = entry.find("atom:link", ns)
            link = safe_text(link_node.attrib.get("href", "") if link_node is not None else "")
            summary = safe_text(entry.findtext("atom:summary", default="", namespaces=ns))
            published = parse_rss_datetime(entry.findtext("atom:updated", default="", namespaces=ns))
            sentiment, score = classify_sentiment(title, summary)
            items.append(
                NewsItem(
                    source=source.name,
                    title=title,
                    link=link,
                    published_at=published,
                    summary=summary[:240],
                    sentiment=sentiment,
                    sentiment_score=score,
                    related_symbols=related_symbols(title, summary),
                )
            )
    return items


def default_sources() -> list[NewsSource]:
    return [
        NewsSource("CoinDesk", DEFAULT_NEWS_SOURCES[0]),
        NewsSource("Cointelegraph", DEFAULT_NEWS_SOURCES[1]),
    ]


class NewsFeedClient:
    def __init__(self, sources: list[NewsSource] | None = None, rate_limiter: RateLimiter | None = None) -> None:
        self.sources = sources or default_sources()
        self.rate_limiter = rate_limiter or RateLimiter(min_interval_seconds=10)

    def fetch(self, max_items_per_source: int = 10) -> NewsFeedResult:
        all_items: list[NewsItem] = []
        errors: list[str] = []
        logs: list[LogRecord] = []
        enabled_sources = [source for source in self.sources if source.enabled]

        for source in enabled_sources:
            key = f"news:{source.name}"
            try:
                waited = self.rate_limiter.wait_if_needed(key)
                xml_text = fetch_text(source.url)
                items = parse_rss(source, xml_text, max_items=max_items_per_source)
                all_items.extend(items)
                self.rate_limiter.success(key)
                logs.append(
                    make_log(
                        LogChannel.NEWS,
                        f"{source.name} haber akışı güncellendi.",
                        LogLevel.INFO,
                        {"source": source.name, "items": len(items), "waited_seconds": waited},
                        f"{source.name} kaynağından {len(items)} haber alındı.",
                    )
                )
            except Exception as exc:
                cooldown = self.rate_limiter.failure(key, exc)
                errors.append(f"{source.name}: {exc}")
                logs.append(
                    make_log(
                        LogChannel.ERROR,
                        f"{source.name} haber akışı alınamadı.",
                        LogLevel.ERROR,
                        {"source": source.name, "error": str(exc), "cooldown_seconds": cooldown},
                        "Haber kaynağından veri alınamadı; rate-limit koruması bekleme süresini artırdı.",
                    )
                )

        all_items.sort(key=lambda item: item.published_at, reverse=True)
        logs.append(
            make_log(
                LogChannel.NEWS,
                "Haber akışı kontrolü tamamlandı.",
                LogLevel.INFO,
                {"total_items": len(all_items), "errors": errors},
                f"Toplam {len(all_items)} haber işlendi. Haberler ilk aşamada sadece bilgilendirme amaçlıdır; işlem kararını doğrudan değiştirmez.",
            )
        )
        return NewsFeedResult(items=all_items, source_count=len(enabled_sources), errors=errors, logs=logs)


def news_items_as_plain_dict(items: list[NewsItem]) -> list[dict[str, Any]]:
    return [
        {
            "source": item.source,
            "title": item.title,
            "link": item.link,
            "published_at": item.published_at,
            "summary": item.summary,
            "sentiment": item.sentiment,
            "sentiment_score": item.sentiment_score,
            "related_symbols": item.related_symbols,
        }
        for item in items
    ]


def summarize_news_for_symbol(items: list[NewsItem], symbol: str) -> dict[str, Any]:
    related = [item for item in items if symbol in item.related_symbols]
    if not related:
        return {
            "symbol": symbol,
            "count": 0,
            "average_sentiment_score": 0.5,
            "summary": "Bu coin için son haber akışında özel bir başlık bulunmadı.",
        }
    avg = sum(item.sentiment_score for item in related) / len(related)
    if avg >= 0.60:
        summary = "Son haber akışı bu coin için görece olumlu görünüyor."
    elif avg <= 0.40:
        summary = "Son haber akışı bu coin için riskli/olumsuz görünüyor."
    else:
        summary = "Son haber akışı bu coin için nötr görünüyor."
    return {
        "symbol": symbol,
        "count": len(related),
        "average_sentiment_score": avg,
        "summary": summary,
    }
