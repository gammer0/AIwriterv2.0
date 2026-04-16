from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


def _strip_quotes(v: str) -> str:
    s = v.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == "'") or (s[0] == s[-1] == '"')):
        return s[1:-1].strip()
    return s


@dataclass(frozen=True)
class Settings:
    app_env: str
    llm_relay_base_url: str
    llm_relay_api_key: Optional[str]
    llm_model: Optional[str]
    disable_llm: bool


def get_settings() -> Settings:
    load_dotenv(override=False)
    app_env = os.getenv("APP_ENV", "dev")
    base_url = _strip_quotes(os.getenv("LLM_RELAY_BASE_URL", "").strip())
    api_key = os.getenv("LLM_RELAY_API_KEY")
    model_raw = os.getenv("LLM_MODEL")
    model = _strip_quotes(model_raw) if model_raw else None
    disable_llm = os.getenv("DISABLE_LLM", "").strip().lower() in {"1", "true", "yes", "on"}
    return Settings(
        app_env=app_env,
        llm_relay_base_url=base_url,
        llm_relay_api_key=api_key,
        llm_model=model,
        disable_llm=disable_llm,
    )
