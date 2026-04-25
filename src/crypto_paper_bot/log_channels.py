from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class LogChannel(str, Enum):
    ALL = "all"
    INDICATOR = "indicator"
    FAMILY = "family"
    AI = "ai"
    TRADE = "trade"
    RISK = "risk"
    DATA = "data"
    ERROR = "error"
    NEWS = "news"
    CONFIDENCE = "confidence"
    RATE_LIMIT = "rate_limit"
    SYSTEM = "system"


class LogLevel(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


CHANNEL_TITLES: dict[LogChannel, str] = {
    LogChannel.ALL: "Tüm Loglar",
    LogChannel.INDICATOR: "İndikatör Logları",
    LogChannel.FAMILY: "Aile Logları",
    LogChannel.AI: "Yapay Zekâ Logları",
    LogChannel.TRADE: "İşlem Logları",
    LogChannel.RISK: "Risk Logları",
    LogChannel.DATA: "Veri Toplama Logları",
    LogChannel.ERROR: "Hata Logları",
    LogChannel.NEWS: "Haber Akışı Logları",
    LogChannel.CONFIDENCE: "Özgüven Logları",
    LogChannel.RATE_LIMIT: "Rate Limit Logları",
    LogChannel.SYSTEM: "Sistem Logları",
}


@dataclass(frozen=True)
class LogRecord:
    created_at: str
    channel: LogChannel
    level: LogLevel
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    user_explanation: str = ""

    def to_event_payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["channel"] = self.channel.value
        data["level"] = self.level.value
        return data


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def make_log(
    channel: LogChannel,
    message: str,
    level: LogLevel = LogLevel.INFO,
    details: dict[str, Any] | None = None,
    user_explanation: str = "",
) -> LogRecord:
    return LogRecord(
        created_at=utc_now(),
        channel=channel,
        level=level,
        message=message,
        details=details or {},
        user_explanation=user_explanation,
    )


def infer_channel_from_legacy_event(level: str, message: str, payload: dict[str, Any] | None = None) -> LogChannel:
    """Map older generic event rows into the new visible log channels.

    The existing database already stores simple events. This function lets the new
    dashboard categorize those old events without a database migration.
    """

    text = f"{level} {message}".lower()
    payload = payload or {}

    if "error" in text or "hata" in text or str(level).upper() == "ERROR":
        return LogChannel.ERROR
    if "veri" in text or "data" in text or "collect" in text or "mum" in text:
        return LogChannel.DATA
    if "eğitim" in text or "model" in text or "ai" in text or "yapay" in text:
        return LogChannel.AI
    if "sanal işlem" in text or "trade" in text or "pozisyon" in text:
        return LogChannel.TRADE
    if "risk" in text or "stop" in text or "zarar kes" in text or "kâr al" in text:
        return LogChannel.RISK
    if "özgüven" in text or "confidence" in text:
        return LogChannel.CONFIDENCE
    if "rate" in text or "limit" in text or "cooldown" in text:
        return LogChannel.RATE_LIMIT
    if "haber" in text or "news" in text:
        return LogChannel.NEWS
    if "indicator" in payload or "rsi" in payload or "ema" in payload or "atr" in payload:
        return LogChannel.INDICATOR
    if "family" in payload or "aile" in payload:
        return LogChannel.FAMILY
    return LogChannel.SYSTEM


def normalize_legacy_event(row: dict[str, Any]) -> LogRecord:
    """Convert one row from storage.latest_events() into a LogRecord."""

    import json

    payload_raw = row.get("payload_json") or "{}"
    try:
        payload = json.loads(payload_raw) if isinstance(payload_raw, str) else dict(payload_raw)
    except Exception:
        payload = {"raw": payload_raw}

    level_text = str(row.get("level") or "INFO").upper()
    try:
        level = LogLevel(level_text)
    except ValueError:
        level = LogLevel.INFO

    message = str(row.get("message") or "")
    channel = infer_channel_from_legacy_event(level.value, message, payload)
    return LogRecord(
        created_at=str(row.get("created_at") or utc_now()),
        channel=channel,
        level=level,
        message=message,
        details=payload,
        user_explanation=explain_log(channel, message, payload),
    )


def explain_log(channel: LogChannel, message: str, details: dict[str, Any] | None = None) -> str:
    details = details or {}

    if channel == LogChannel.DATA:
        rows = details.get("rows")
        if rows is not None:
            return f"Sistem piyasadan yeni mum verileri topladı. Kaydedilen veri sayısı: {rows}."
        return "Sistem piyasa verisi toplamaya çalıştı."

    if channel == LogChannel.AI:
        samples = details.get("trained_samples")
        acc = details.get("accuracy")
        if samples is not None:
            if acc is not None:
                return f"Yapay zekâ modeli {samples} örnekle eğitildi. Geçici doğruluk oranı yaklaşık %{float(acc) * 100:.1f}."
            return f"Yapay zekâ modeli {samples} örnekle eğitildi."
        return "Yapay zekâ modeli veya tahmin sistemiyle ilgili bir kayıt oluştu."

    if channel == LogChannel.TRADE:
        return "Sanal işlem motoru bir pozisyonu açtı, kapattı veya kontrol etti."

    if channel == LogChannel.RISK:
        return "Risk motoru miktar, zarar kes veya kâr al seviyelerini değerlendirdi."

    if channel == LogChannel.INDICATOR:
        return "İndikatör motoru EMA, RSI, ATR veya hacim gibi teknik göstergeleri hesapladı."

    if channel == LogChannel.FAMILY:
        return "Aile motoru trend, momentum, hacim veya risk ailelerinin toplam kararını hesapladı."

    if channel == LogChannel.CONFIDENCE:
        return "Özgüven motoru işlem veya sistem güven puanını hesapladı."

    if channel == LogChannel.RATE_LIMIT:
        return "Rate-limit koruması API istek hızını kontrol etti."

    if channel == LogChannel.NEWS:
        return "Haber akışı sistemi yeni haberleri veya duyuruları kontrol etti."

    if channel == LogChannel.ERROR:
        return "Sistem bir hata yakaladı. Bu hata işlem güvenliğini korumak için loglandı."

    return "Sistem genel bir işlem kaydı oluşturdu."


def filter_logs(records: list[LogRecord], channel: LogChannel) -> list[LogRecord]:
    if channel == LogChannel.ALL:
        return records
    return [record for record in records if record.channel == channel]


def group_logs(records: list[LogRecord]) -> dict[LogChannel, list[LogRecord]]:
    grouped: dict[LogChannel, list[LogRecord]] = {channel: [] for channel in LogChannel}
    for record in records:
        grouped[LogChannel.ALL].append(record)
        grouped[record.channel].append(record)
    return grouped


def channel_title(channel: LogChannel | str) -> str:
    if isinstance(channel, str):
        channel = LogChannel(channel)
    return CHANNEL_TITLES.get(channel, channel.value)
