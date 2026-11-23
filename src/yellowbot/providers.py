"""Provider-agnostic chat backends. Standard library only.

Every provider implements ``chat(system, messages) -> str`` where messages is a list of
{"role": "user"|"assistant", "content": str}. The master prompt is plain text, so it works the
same on every backend.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

PRESETS = {
    # name: (base_url, env var holding the key or None, default model)
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY", "openrouter/auto"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "ollama": ("http://localhost:11434/v1", None, "llama3.1"),
    "lmstudio": ("http://localhost:1234/v1", None, "local-model"),
    "compat": ("", "YB_API_KEY", ""),  # any OpenAI-compatible server: set YB_BASE_URL + YB_MODEL
}
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_DEFAULT_MODEL = "claude-sonnet-5-5"


class ProviderError(RuntimeError):
    pass


def _post(url: str, headers: dict, body: dict, timeout: float) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json", **headers}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise ProviderError(f"HTTP {e.code} from {url}: {detail}") from e
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise ProviderError(f"Could not reach {url}: {e}") from e


class OpenAICompatProvider:
    """OpenAI, OpenRouter, Groq, Ollama, LM Studio, vLLM, llama.cpp server, and friends."""

    def __init__(self, name: str, base_url: str, api_key: str | None, model: str,
                 temperature: float = 0.8, timeout: float = 120):
        if not base_url:
            raise ProviderError("No base URL. Set YB_BASE_URL or --base-url.")
        if not model:
            raise ProviderError("No model. Set YB_MODEL or --model.")
        self.name, self.base_url, self.api_key = name, base_url.rstrip("/"), api_key
        self.model, self.temperature, self.timeout = model, temperature, timeout

    def chat(self, system: str, messages: list[dict]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post(
            f"{self.base_url}/chat/completions",
            headers,
            {"model": self.model, "temperature": self.temperature,
             "messages": [{"role": "system", "content": system}, *messages]},
            self.timeout,
        )
        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError(f"Unexpected response shape: {str(data)[:300]}") from e


class AnthropicProvider:
    def __init__(self, api_key: str | None, model: str, temperature: float = 0.8,
                 max_tokens: int = 1500, timeout: float = 120):
        if not api_key:
            raise ProviderError("Set ANTHROPIC_API_KEY (or YB_API_KEY) to use the anthropic provider.")
        self.name, self.api_key, self.model = "anthropic", api_key, model
        self.temperature, self.max_tokens, self.timeout = temperature, max_tokens, timeout

    def chat(self, system: str, messages: list[dict]) -> str:
        data = _post(
            ANTHROPIC_URL,
            {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
            {"model": self.model, "max_tokens": self.max_tokens, "temperature": self.temperature,
             "system": system, "messages": messages},
            self.timeout,
        )
        try:
            return "".join(b["text"] for b in data["content"] if b.get("type") == "text").strip()
        except (KeyError, TypeError) as e:
            raise ProviderError(f"Unexpected response shape: {str(data)[:300]}") from e


def make_provider(name: str | None = None, model: str | None = None, base_url: str | None = None,
                  temperature: float = 0.8):
    """Build a provider from args and environment. Returns None for the offline engine."""
    name = (name or os.environ.get("YB_PROVIDER") or "offline").lower()
    model = model or os.environ.get("YB_MODEL")
    if name == "offline":
        return None
    if name == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("YB_API_KEY")
        return AnthropicProvider(key, model or ANTHROPIC_DEFAULT_MODEL, temperature)
    if name in PRESETS:
        url, key_env, default_model = PRESETS[name]
        url = base_url or os.environ.get("YB_BASE_URL") or url
        key = os.environ.get(key_env) if key_env else os.environ.get("YB_API_KEY")
        if key_env and not key:
            raise ProviderError(f"Set {key_env} to use the {name} provider.")
        return OpenAICompatProvider(name, url, key, model or default_model, temperature)
    raise ProviderError(f"Unknown provider '{name}'. Options: offline, anthropic, {', '.join(PRESETS)}")
