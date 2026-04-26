from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from crypto_paper_bot.log_channels import LogChannel, LogLevel, LogRecord, make_log
from crypto_paper_bot.rate_limiter import RateLimiter


GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"

# Model names are configurable because providers can rename or retire models.
# The first model in the list is always treated as the strongest/preferred model.
DEFAULT_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


@dataclass(frozen=True)
class LLMRequest:
    purpose: str
    messages: list[LLMMessage]
    temperature: float = 0.2
    max_tokens: int = 700


@dataclass(frozen=True)
class LLMResponse:
    ok: bool
    content: str
    provider: str
    model: str
    used_fallback: bool
    local_fallback: bool
    error: str | None = None
    logs: list[LogRecord] = field(default_factory=list)


@dataclass(frozen=True)
class GroqRouterConfig:
    api_key_env: str = "GROQ_API_KEY"
    models_env: str = "GROQ_MODEL_ORDER"
    min_interval_seconds: int = 10
    timeout_seconds: int = 30


def _model_order(config: GroqRouterConfig) -> list[str]:
    raw = os.environ.get(config.models_env, "").strip()
    if not raw:
        return list(DEFAULT_GROQ_MODELS)
    models = [item.strip() for item in raw.split(",") if item.strip()]
    return models or list(DEFAULT_GROQ_MODELS)


def _local_explanation(request: LLMRequest, reason: str) -> str:
    if request.purpose == "decision_explanation":
        return (
            "Yerel açıklama: Yapay zekâ servisinden cevap alınamadı. "
            "Sistem yine de yerel indikatör, özgüven ve risk motoru kayıtlarına göre çalışmaya devam eder. "
            f"LLM yedeğine düşme nedeni: {reason}"
        )
    if request.purpose == "news_summary":
        return (
            "Yerel açıklama: Haber özeti için yapay zekâ servisine ulaşılamadı. "
            "Haberler ham başlık ve basit pozitif/nötr/negatif sınıflandırma ile gösterilecek."
        )
    if request.purpose == "assistant_help":
        return (
            "Yerel açıklama: Şu anda Groq yanıtı alınamadı. "
            "Paneldeki değerleri şöyle okuyabilirsin: Sistem Özgüveni genel sağlık puanıdır; "
            "İşlem Özgüveni tek bir işlem adayının güven puanıdır; İndikatör Skoru teknik göstergelerin özetidir."
        )
    return f"Yerel açıklama: LLM servisi kullanılamadı. Neden: {reason}"


def _messages_payload(messages: list[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]


def _is_quota_or_rate_error(status_code: int | None, body: str) -> bool:
    text = body.lower()
    return status_code in {429, 402, 403} or "rate" in text or "quota" in text or "limit" in text


class GroqLLMRouter:
    """Small Groq-compatible router with model fallback.

    Important boundary:
    - This router must not place trades.
    - This router must not override the risk engine.
    - It is only for explanations, summaries, and assistant text.
    """

    def __init__(
        self,
        config: GroqRouterConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.config = config or GroqRouterConfig()
        self.rate_limiter = rate_limiter or RateLimiter(self.config.min_interval_seconds)
        self.models = _model_order(self.config)

    def _call_groq(self, model: str, request_data: LLMRequest, api_key: str) -> str:
        payload = {
            "model": model,
            "messages": _messages_payload(request_data.messages),
            "temperature": request_data.temperature,
            "max_tokens": request_data.max_tokens,
        }
        encoded = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            GROQ_CHAT_COMPLETIONS_URL,
            data=encoded,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "crypto-paper-bot/0.1",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            choices = data.get("choices") or []
            if not choices:
                raise RuntimeError("Groq response did not contain choices")
            message = choices[0].get("message") or {}
            content = message.get("content")
            if not content:
                raise RuntimeError("Groq response did not contain message content")
            return str(content)

    def complete(self, request_data: LLMRequest) -> LLMResponse:
        api_key = os.environ.get(self.config.api_key_env, "").strip()
        logs: list[LogRecord] = []

        if not api_key:
            explanation = _local_explanation(request_data, "GROQ_API_KEY tanımlı değil")
            logs.append(
                make_log(
                    LogChannel.AI,
                    "Groq kullanılmadı; API anahtarı yok.",
                    LogLevel.WARNING,
                    {"purpose": request_data.purpose},
                    "Groq API anahtarı olmadığı için yerel açıklama motoru kullanıldı.",
                )
            )
            return LLMResponse(
                ok=True,
                content=explanation,
                provider="local",
                model="local_fallback",
                used_fallback=True,
                local_fallback=True,
                error="missing_api_key",
                logs=logs,
            )

        last_error = "unknown_error"
        for index, model in enumerate(self.models):
            key = f"groq:{model}"
            try:
                waited = self.rate_limiter.wait_if_needed(key)
                content = self._call_groq(model, request_data, api_key)
                self.rate_limiter.success(key)
                logs.append(
                    make_log(
                        LogChannel.AI,
                        "Groq model cevabı alındı.",
                        LogLevel.SUCCESS,
                        {
                            "provider": "groq",
                            "model": model,
                            "purpose": request_data.purpose,
                            "waited_seconds": waited,
                            "used_fallback": index > 0,
                        },
                        f"Groq üzerinden {model} modeli cevap verdi.",
                    )
                )
                return LLMResponse(
                    ok=True,
                    content=content,
                    provider="groq",
                    model=model,
                    used_fallback=index > 0,
                    local_fallback=False,
                    logs=logs,
                )
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
                last_error = f"HTTP {exc.code}: {body[:300]}"
                cooldown = self.rate_limiter.failure(key, last_error)
                level = LogLevel.WARNING if _is_quota_or_rate_error(exc.code, body) else LogLevel.ERROR
                logs.append(
                    make_log(
                        LogChannel.AI,
                        "Groq model çağrısı başarısız oldu; sıradaki modele geçiliyor.",
                        level,
                        {
                            "provider": "groq",
                            "model": model,
                            "status_code": exc.code,
                            "cooldown_seconds": cooldown,
                            "purpose": request_data.purpose,
                        },
                        "Groq modelinde kota, rate-limit veya servis hatası oluştu. Sistem sıradaki modeli deneyecek.",
                    )
                )
                continue
            except Exception as exc:
                last_error = str(exc)
                cooldown = self.rate_limiter.failure(key, exc)
                logs.append(
                    make_log(
                        LogChannel.AI,
                        "Groq model çağrısı hata verdi; sıradaki modele geçiliyor.",
                        LogLevel.ERROR,
                        {
                            "provider": "groq",
                            "model": model,
                            "error": str(exc),
                            "cooldown_seconds": cooldown,
                            "purpose": request_data.purpose,
                        },
                        "Groq modelinden yanıt alınamadı. Sistem varsa sıradaki modeli deneyecek.",
                    )
                )
                continue

        local = _local_explanation(request_data, last_error)
        logs.append(
            make_log(
                LogChannel.AI,
                "Tüm Groq modelleri başarısız oldu; yerel açıklama kullanıldı.",
                LogLevel.WARNING,
                {"purpose": request_data.purpose, "error": last_error, "models": self.models},
                "Tüm Groq modelleri hata verdiği için güvenli yerel açıklama motoru kullanıldı.",
            )
        )
        return LLMResponse(
            ok=True,
            content=local,
            provider="local",
            model="local_fallback",
            used_fallback=True,
            local_fallback=True,
            error=last_error,
            logs=logs,
        )


def simple_assistant_prompt(question: str, context: dict[str, Any] | None = None) -> LLMRequest:
    context_text = json.dumps(context or {}, ensure_ascii=False, indent=2)
    return LLMRequest(
        purpose="assistant_help",
        messages=[
            LLMMessage(
                role="system",
                content=(
                    "Sen kripto paper-trade panelindeki değerleri sade Türkçe açıklayan bir yardımcı asistansın. "
                    "Yatırım tavsiyesi verme. Gerçek para işlemi önermeden, sadece sistemin ne yaptığını açıkla."
                ),
            ),
            LLMMessage(
                role="user",
                content=f"Soru: {question}\n\nPanel bağlamı:\n{context_text}",
            ),
        ],
        temperature=0.2,
        max_tokens=700,
    )


def llm_response_as_plain_dict(response: LLMResponse) -> dict[str, Any]:
    return {
        "ok": response.ok,
        "content": response.content,
        "provider": response.provider,
        "model": response.model,
        "used_fallback": response.used_fallback,
        "local_fallback": response.local_fallback,
        "error": response.error,
    }
