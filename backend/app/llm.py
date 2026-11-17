"""Minimal client for OpenAI-compatible chat-completion APIs.

``LLM_MODEL`` is ``<provider>/<model id>``; the provider picks the base URL and the
API-key env var. Groq, OpenAI, Gemini and Anthropic all expose this API shape.

    groq/openai/gpt-oss-120b         GROQ_API_KEY
    openai/gpt-4o-mini               OPENAI_API_KEY
    gemini/gemini-2.0-flash          GEMINI_API_KEY
    anthropic/claude-sonnet-5-5      ANTHROPIC_API_KEY

``LLM_API_BASE`` overrides the URL (e.g. a self-hosted vLLM / Ollama server).
Cost is recorded only if ``LLM_PRICE_IN`` / ``LLM_PRICE_OUT`` (USD per 1M tokens) are set.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings

PROVIDERS: dict[str, tuple[str, str]] = {
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1", "ANTHROPIC_API_KEY"),
}


class LLMError(RuntimeError):
    pass


@dataclass
class LLMReply:
    message: dict[str, Any]  # OpenAI-format assistant message (content, tool_calls)
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    cost_usd: float


def _endpoint() -> tuple[str, str, str]:
    s = get_settings()
    provider, _, model = s.llm_model.partition("/")
    if provider not in PROVIDERS or not model:
        raise LLMError(f"LLM_MODEL must look like '<provider>/<model>' with provider in {sorted(PROVIDERS)}")
    base, key_var = PROVIDERS[provider]
    key = os.environ.get(key_var) or _env_file_value(key_var)
    if not key:
        raise LLMError(f"{key_var} is not set in backend/.env")
    return (s.llm_api_base or base).rstrip("/"), key, model


def _env_file_value(name: str) -> str | None:
    """Keys live in backend/.env; pydantic-settings ignores unknown keys, so read them here."""
    from app.config import BACKEND_DIR

    path = BACKEND_DIR / ".env"
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        k, sep, v = line.strip().partition("=")
        if sep and k.strip() == name:
            return v.strip().strip('"').strip("'") or None
    return None


def _retry_after(r: httpx.Response) -> float:
    try:
        return float(r.headers.get("retry-after", ""))
    except ValueError:
        m = re.search(r"try again in ([\d.]+)s", r.text)
        return float(m.group(1)) if m else 5.0


def _post(base: str, key: str, body: dict[str, Any]) -> httpx.Response:
    return httpx.post(f"{base}/chat/completions", json=body, timeout=45,
                      headers={"Authorization": f"Bearer {key}"})


def chat(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, *,
         temperature: float = 0.3, max_tokens: int = 700) -> LLMReply:
    """One completion. On a rate limit: wait if the provider asks for <= 12 s, else
    (or if still limited) try ``LLM_FALLBACK_MODEL`` once."""
    base, key, model = _endpoint()
    s = get_settings()
    models = [model]
    if s.llm_fallback_model:
        fb_provider, _, fb_model = s.llm_fallback_model.partition("/")
        if fb_provider == s.llm_model.partition("/")[0] and fb_model and fb_model != model:
            models.append(fb_model)

    last = "no attempt"
    for m in models:
        body: dict[str, Any] = {"model": m, "messages": messages, "temperature": temperature,
                                "max_tokens": max_tokens}
        if "gpt-oss" in m:
            body["reasoning_effort"] = "low"  # fewer hidden reasoning tokens -> faster, cheaper
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        for attempt in range(2):
            started = time.perf_counter()
            try:
                r = _post(base, key, body)
            except httpx.HTTPError as exc:
                last = f"network error: {exc}"
                continue
            if r.status_code == 429:
                wait = _retry_after(r)
                last = f"rate limited on {m} (retry in {wait:.0f}s)"
                if attempt == 0 and wait <= 12:
                    time.sleep(wait + 0.3)
                    continue
                break  # next model
            if r.status_code >= 500:
                last = f"HTTP {r.status_code}"
                time.sleep(1.0)
                continue
            if r.status_code >= 400:
                raise LLMError(f"HTTP {r.status_code}: {r.text[:300]}")
            data = r.json()
            usage = data.get("usage") or {}
            pin, pout = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
            cost = (pin * s.llm_price_in + pout * s.llm_price_out) / 1_000_000
            msg = data["choices"][0]["message"]
            msg.pop("reasoning", None)  # don't send hidden reasoning back in later turns
            return LLMReply(message=msg, prompt_tokens=pin, completion_tokens=pout,
                            latency_ms=int((time.perf_counter() - started) * 1000), cost_usd=cost)
    raise LLMError(f"LLM request failed: {last}")
