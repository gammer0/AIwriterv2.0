from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class AgentResult:
    data: Dict[str, Any]


class Agent:
    name: str = "agent"

    def run(self, text: str, **kwargs: Any) -> AgentResult:
        raise NotImplementedError
