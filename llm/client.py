from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from llm.relay_proxy import RelayConfig, RelayProxy


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: Optional[Dict[str, Any]] = None


class LLMClient:
    """
    接入中转 API 的统一客户端（兼容 OpenAI Chat Completions 风格的中转）。
    """

    def __init__(self, relay: RelayProxy, *, default_model: Optional[str] = None):
        self._relay = relay
        self._default_model = default_model

    @staticmethod
    def build(
        *,
        base_url: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_s: float = 60.0,
    ) -> "LLMClient":
        cfg = RelayConfig(base_url=base_url, api_key=api_key, model=model)
        relay = RelayProxy(cfg, timeout_s=timeout_s)
        return LLMClient(relay, default_model=model)

    @property
    def default_model(self) -> Optional[str]:
        return self._default_model or self._relay._config.model

    def chat(self, user_text: str, *, system: Optional[str] = None, model: Optional[str] = None) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user_text})

        payload: Dict[str, Any] = {
            "model": model or self.default_model or "",
            "messages": messages,
        }
        payload = {k: v for k, v in payload.items() if v not in ("", None)}

        data = self._relay.chat_completions(payload)
        text = _extract_chat_text(data)
        return LLMResponse(text=text, raw=data)


def _extract_chat_text(data: Dict[str, Any]) -> str:
    """
    兼容多种中转返回：
    - OpenAI chat.completions: choices[0].message.content
    - 兜底：choices[0].text 或 data["text"]
    """
    try:
        choices = data.get("choices") or []
        if choices:
            c0 = choices[0] or {}
            msg = c0.get("message")
            if isinstance(msg, dict) and isinstance(msg.get("content"), str):
                return msg["content"]
            if isinstance(c0.get("text"), str):
                return c0["text"]
    except Exception:
        pass
    if isinstance(data.get("text"), str):
        return data["text"]
    return ""
