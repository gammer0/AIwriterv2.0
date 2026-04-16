from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _ensure_repo_root_on_syspath() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def _strip_quotes(v: str) -> str:
    s = v.strip()
    if len(s) >= 2 and ((s[0] == s[-1] == "'") or (s[0] == s[-1] == '"')):
        return s[1:-1].strip()
    return s


def main() -> None:
    _ensure_repo_root_on_syspath()
    from llm.client import LLMClient

    load_dotenv(override=False)
    base_url = _strip_quotes(os.getenv("LLM_RELAY_BASE_URL", "").strip())
    api_key = os.getenv("LLM_RELAY_API_KEY")
    model_raw = os.getenv("LLM_MODEL")
    model = _strip_quotes(model_raw) if model_raw else None

    if not base_url:
        raise SystemExit("LLM_RELAY_BASE_URL is empty")

    client = LLMClient.build(base_url=base_url, api_key=api_key, model=model)
    resp = client.chat("请用一句话介绍你自己。", system="你是一个简洁的助手。")
    print(resp.text)


if __name__ == "__main__":
    main()
