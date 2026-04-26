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
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

DEFAULT_GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "gemma2-9b-it",
]

PREFERRED_MODEL_KEYWORDS = [
    "70b",
    "mixtral",
    "llama-3.3",
    "llama-3.1",
    "llama3",
    "qwen",
    "gemma",
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
    available_models: list[str] = field(default_factory=list)
    logs: list[LogRecord] = field(default_factory=list)


@dataclass(frozen=True)
class GroqRouterConfig:
    api_key_env: str = "GROQ_API_KEY"
    models_env: str = "GROQ_MODEL_ORDER"
    min_interval_seconds: int = 10
    timeout_seconds: int = 30
    auto_discover_models: bool = True


def _manual_model_order(config: GroqRouterConfig) -> list[str] | None:
    raw = os.environ.get(config.models_env, "").strip()
    if not raw:
        return None
    models = [item.strip() for item in raw.split(",") if item.strip()]
    return models or None


def _model_rank(model_id: str) -> tuple[int, str]:
    lower = model_id.lower()
    for index, keyword in enumerate(PREFERRED_MODEL_KEYWORDS):
        if keyword in lower:
            return (index, lower)
    return (len(PREFERRED_MODEL_KEYWORDS), lower)


def _local_explanation(request: LLMRequest, reason: str) -> str:
    if request.purpose == "decision_explanation":
        return (
            "Yerel açıklama: Yapay zekâ servisinden cevap alınamadı. "
            "Sistem yine de yerel indikatör, işlem özgüveni ve risk motoru kayıtlarına göre çalışmaya devam eder. "
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
            "Paneldeki değerleri şöyle okuyabilirsin: Sistem Özgüveni kapanmış sanal işlemlerdeki başarı oranıdır. "
            "İşlem Özgüveni tek bir işlem adayının bileşen puanıdır. İndikatör Skoru teknik göstergelerin özetidir."
        )
    return f"Yerel açıklama: LLM servisi kullanılamadı. Neden: {reason}"


def _messages_payload(messages: list[LLMMessage]) -> list[dict[str, str]]:
    return [{"role": message.role, "content": message.content} for message in messages]


def _is_quota_or_rate_error(status_code: int | None, body: str) -> bool:
    text = body.lower()
    return status_code in {429, 402, 403} or "rate" in text or "quota" in text or "limit" in text


class GroqLLMRouter:
    """Groq-compatible router with auto model discovery and fallback.

    Boundary:
    - This router never places trades.
    - This router never overrides the risk engine.
    - It only produces explanations, summaries, and assistant text.
    """

    def __init__(
        self,
        config: GroqRouterConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.config = config or GroqRouterConfig()
        self.rate_limiter = rate_limiter or RateLimiter(self.config.min_interval_seconds)
        self.models = _manual_model_order(self.config) or list(DEFAULT_GROQ_MODELS)

    def discover_models(self, api_key: str) -> list[str]:
        manual = _manual_model_order(self.config)
        if manual:
            self.models = manual
            return self.models
        if not self.config.auto_discover_models:
            return self.models
        key = "groq:models"
        self.rate_limiter.wait_if_needed(key)
        req = urllib.request.Request(
            GROQ_MODELS_URL,
            headers={"Authorization": f"Bearer {api_key}", "User-Agent": "crypto-paper-bot/0.1"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
        model_ids = [str(item.get("id")) for item in data.get("data", []) if item.get("id")]
        if model_ids:
            self.models = sorted(model_ids, key=_model_rank)
        self.rate_limiter.success(key)
        return self.models

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
            return LLMResponse(True, explanation, "local", "local_fallback", True, True, "missing_api_key", [], logs)

        try:
            discovered = self.discover_models(api_key)
            logs.append(
                make_log(
                    LogChannel.AI,
                    "Groq model listesi alındı.",
                    LogLevel.INFO,
                    {"models": discovered, "model_count": len(discovered)},
                    f"Groq üzerinden {len(discovered)} model bulundu. Sistem listedeki en güçlü adaydan başlayacak.",
                )
            )
        except Exception as exc:
            cooldown = self.rate_limiter.failure("groq:models", exc)
            logs.append(
                make_log(
                    LogChannel.AI,
                    "Groq model listesi alınamadı; varsayılan liste kullanılacak.",
                    LogLevel.WARNING,
                    {"error": str(exc), "cooldown_seconds": cooldown, "models": self.models},
                    "Groq model listesi çekilemediği için varsayılan model sırası kullanılacak.",
                )
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
                            "available_models": self.models,
                        },
                        f"Groq üzerinden {model} modeli cevap verdi.",
                    )
                )
                return LLMResponse(True, content, "groq", model, index > 0, False, None, list(self.models), logs)
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
                        {"provider": "groq", "model": model, "status_code": exc.code, "cooldown_seconds": cooldown, "purpose": request_data.purpose},
                        "Groq modelinde kota, rate-limit veya servis hatası oluştu. Sistem sıradaki modeli deneyecek.",
                    )
                )
            except Exception as exc:
                last_error = str(exc)
                cooldown = self.rate_limiter.failure(key, exc)
                logs.append(
                    make_log(
                        LogChannel.AI,
                        "Groq model çağrısı hata verdi; sıradaki modele geçiliyor.",
                        LogLevel.ERROR,
                        {"provider": "groq", "model": model, "error": str(exc), "cooldown_seconds": cooldown, "purpose": request_data.purpose},
                        "Groq modelinden yanıt alınamadı. Sistem varsa sıradaki modeli deneyecek.",
                    )
                )

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
        return LLMResponse(True, local, "local", "local_fallback", True, True, last_error, list(self.models), logs)


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
            LLMMessage(role="user", content=f"Soru: {question}\n\nPanel bağlamı:\n{context_text}"),
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
        "available_models": response.available_models,
    }
