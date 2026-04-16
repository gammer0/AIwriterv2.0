from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RelayConfig:
    base_url: str
    api_key: Optional[str] = None
    model: Optional[str] = None
