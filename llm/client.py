from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class LLMResponse:
    text: str
    raw: Optional[Dict[str, Any]] = None


class LLMClient:
    """
    预留：接入中转 API 的统一客户端。
    当前工作流使用骨架逻辑，不会真实请求 LLM。
    """

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        raise NotImplementedError("LLMClient is not wired yet.")
