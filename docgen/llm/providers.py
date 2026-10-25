"""Provider-agnostic chat client (stdlib HTTP).

Supports OpenAI-compatible endpoints (OpenAI, xAI, DeepSeek, OpenRouter, Ollama,
Groq, Together, Fireworks, local vLLM/llama.cpp) plus Anthropic Messages and
Google Gemini generateContent.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "ToolHunt-docgen/1.0 (+https://github.com/canonrebel04/ToolHunt)"

# name -> (default_base_url, env_key_names, default_model, kind)
# kind: openai | anthropic | gemini
PROVIDERS: dict[str, tuple[str, tuple[str, ...], str, str]] = {
    "openai": ("https://api.openai.com/v1", ("OPENAI_API_KEY", "TOOLHUNT_LLM_API_KEY"), "gpt-4o-mini", "openai"),
    "xai": ("https://api.x.ai/v1", ("XAI_API_KEY", "TOOLHUNT_LLM_API_KEY"), "grok-4-fast-non-reasoning", "openai"),
    "deepseek": ("https://api.deepseek.com/v1", ("DEEPSEEK_API_KEY", "TOOLHUNT_LLM_API_KEY"), "deepseek-chat", "openai"),
    "openrouter": ("https://openrouter.ai/api/v1", ("OPENROUTER_API_KEY", "TOOLHUNT_LLM_API_KEY"), "openrouter/auto", "openai"),
    "groq": ("https://api.groq.com/openai/v1", ("GROQ_API_KEY", "TOOLHUNT_LLM_API_KEY"), "llama-3.3-70b-versatile", "openai"),
    "together": ("https://api.together.xyz/v1", ("TOGETHER_API_KEY", "TOOLHUNT_LLM_API_KEY"), "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "openai"),
    "fireworks": ("https://api.fireworks.ai/inference/v1", ("FIREWORKS_API_KEY", "TOOLHUNT_LLM_API_KEY"), "accounts/fireworks/models/llama-v3p1-8b-instruct", "openai"),
    "ollama": ("http://127.0.0.1:11434/v1", ("OLLAMA_API_KEY", "TOOLHUNT_LLM_API_KEY"), "llama3.2", "openai"),
    "local": ("http://127.0.0.1:11434/v1", ("TOOLHUNT_LLM_API_KEY",), "llama3.2", "openai"),
    "custom": ("", ("TOOLHUNT_LLM_API_KEY", "OPENAI_API_KEY"), "gpt-4o-mini", "openai"),
    "anthropic": ("https://api.anthropic.com", ("ANTHROPIC_API_KEY", "TOOLHUNT_LLM_API_KEY"), "claude-3-5-haiku-latest", "anthropic"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta", ("GEMINI_API_KEY", "GOOGLE_API_KEY", "TOOLHUNT_LLM_API_KEY"), "gemini-2.0-flash", "gemini"),
}


def list_providers() -> list[str]:
    return sorted(PROVIDERS)


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str
    kind: str
    timeout: int = 120

    @classmethod
    def from_env(cls, provider: str | None = None) -> LLMConfig:
        name = (provider or os.environ.get("TOOLHUNT_LLM_PROVIDER") or "openai").strip().lower()
        if name not in PROVIDERS:
            raise ValueError(f"Unknown provider {name!r}; choose one of {', '.join(list_providers())}")
        default_base, key_names, default_model, kind = PROVIDERS[name]
        base = (os.environ.get("TOOLHUNT_LLM_BASE_URL") or default_base).rstrip("/")
        if name == "custom" and not base:
            raise ValueError("custom provider requires TOOLHUNT_LLM_BASE_URL")
        model = os.environ.get("TOOLHUNT_LLM_MODEL") or default_model
        api_key = ""
        for kn in key_names:
            api_key = os.environ.get(kn) or ""
            if api_key:
                break
        # Local/Ollama often need no key
        if not api_key and name not in ("ollama", "local"):
            raise ValueError(
                f"No API key found for {name}. Set one of: {', '.join(key_names)}"
            )
        timeout = int(os.environ.get("TOOLHUNT_LLM_TIMEOUT", "120"))
        return cls(provider=name, model=model, api_key=api_key, base_url=base, kind=kind, timeout=timeout)


def _post_json(url: str, payload: dict, headers: dict, timeout: int) -> dict:
    data = json.dumps(payload).encode("utf-8")
    hdrs = {"User-Agent": USER_AGENT, "Content-Type": "application/json", **headers}
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")[:500]
        raise RuntimeError(f"LLM HTTP {e.code}: {err}") from e
    return json.loads(body)


def _openai_chat(cfg: LLMConfig, messages: list[dict], *, temperature: float = 0.2) -> str:
    url = f"{cfg.base_url}/chat/completions"
    headers = {}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    if cfg.provider == "openrouter":
        headers.setdefault("HTTP-Referer", "https://github.com/canonrebel04/ToolHunt")
        headers.setdefault("X-Title", "ToolHunt")
    payload = {
        "model": cfg.model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    # Some local servers reject response_format — retry without it on failure
    try:
        data = _post_json(url, payload, headers, cfg.timeout)
    except RuntimeError as e:
        if "response_format" in str(e).lower() or "400" in str(e):
            payload.pop("response_format", None)
            data = _post_json(url, payload, headers, cfg.timeout)
        else:
            raise
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"Empty LLM response: {data!r}"[:400])
    msg = choices[0].get("message") or {}
    content = msg.get("content") or ""
    if isinstance(content, list):
        content = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content)


def _anthropic_chat(cfg: LLMConfig, messages: list[dict], *, temperature: float = 0.2) -> str:
    url = f"{cfg.base_url}/v1/messages"
    system = ""
    converted = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
            continue
        converted.append({"role": m["role"], "content": m["content"]})
    payload = {
        "model": cfg.model,
        "max_tokens": 4096,
        "temperature": temperature,
        "messages": converted,
    }
    if system:
        payload["system"] = system
    headers = {
        "x-api-key": cfg.api_key,
        "anthropic-version": "2023-06-01",
    }
    data = _post_json(url, payload, headers, cfg.timeout)
    parts = data.get("content") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("type") == "text"]
    if not texts:
        raise RuntimeError(f"Empty Anthropic response: {data!r}"[:400])
    return "\n".join(texts)


def _gemini_chat(cfg: LLMConfig, messages: list[dict], *, temperature: float = 0.2) -> str:
    # Flatten to a single user prompt with system preamble (simple + reliable)
    system = ""
    chunks = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            chunks.append(f"{m['role'].upper()}: {m['content']}")
    prompt = (system + "\n\n" if system else "") + "\n\n".join(chunks)
    url = f"{cfg.base_url}/models/{cfg.model}:generateContent?key={cfg.api_key}"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }
    data = _post_json(url, payload, {}, cfg.timeout)
    cands = data.get("candidates") or []
    if not cands:
        raise RuntimeError(f"Empty Gemini response: {data!r}"[:400])
    parts = (((cands[0] or {}).get("content") or {}).get("parts")) or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
    if not texts:
        raise RuntimeError(f"Empty Gemini parts: {data!r}"[:400])
    return "\n".join(texts)


def chat_completion(messages: list[dict], *, config: LLMConfig | None = None, temperature: float = 0.2) -> str:
    """Return the assistant text for a chat request."""
    cfg = config or LLMConfig.from_env()
    if cfg.kind == "openai":
        return _openai_chat(cfg, messages, temperature=temperature)
    if cfg.kind == "anthropic":
        return _anthropic_chat(cfg, messages, temperature=temperature)
    if cfg.kind == "gemini":
        return _gemini_chat(cfg, messages, temperature=temperature)
    raise ValueError(f"Unsupported kind {cfg.kind}")
