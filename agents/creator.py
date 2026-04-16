from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import Agent, AgentResult
from app.settings import get_settings
from llm.client import LLMClient


class CreatorAgent(Agent):
    name = "creator"

    def run(
        self,
        user_text: str,
        *,
        guide: Dict[str, Any],
        prev_draft: Optional[str] = None,
        notes: Optional[List[str]] = None,
        **kwargs: object,
    ) -> AgentResult:
        settings = get_settings()
        system_prompt = _load_system_prompt(Path("prompts") / "创作agent.md")

        payload = {
            "user_text": user_text,
            "guide": guide,
            "prev_draft": prev_draft,
            "notes": notes or [],
        }

        draft: Optional[Dict[str, Any]] = None
        raw: Optional[Dict[str, Any]] = None
        llm_error: Optional[str] = None

        if settings.llm_relay_base_url:
            try:
                client = LLMClient.build(
                    base_url=settings.llm_relay_base_url,
                    api_key=settings.llm_relay_api_key,
                    model=settings.llm_model,
                    timeout_s=60.0,
                )
                resp = client.chat(json.dumps(payload, ensure_ascii=False), system=system_prompt)
                raw = resp.raw
                draft = _parse_creator_json(resp.text)
            except Exception as e:
                llm_error = str(e)

        if draft is None:
            draft = _fallback_creator(user_text, guide, prev_draft=prev_draft, notes=notes or [])

        return AgentResult(
            data={
                **draft,
                "llm": {
                    "enabled": bool(settings.llm_relay_base_url),
                    "model": settings.llm_model,
                    "error": llm_error,
                    "raw": raw,
                },
            }
        )


def _load_system_prompt(path: Path) -> str:
    raw = path.read_text(encoding="utf-8")
    m = re.search(r"BEGIN_SYSTEM_PROMPT\s*(.*?)\s*END_SYSTEM_PROMPT", raw, flags=re.DOTALL)
    if not m:
        raise ValueError(f"System prompt markers not found in {path}")
    return m.group(1).strip()


def _extract_first_json_object(s: str) -> str:
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return s
    s = re.sub(r"^```(?:json)?\\s*", "", s.strip(), flags=re.IGNORECASE)
    s = re.sub(r"\\s*```$", "", s.strip())

    start = s.find("{")
    if start < 0:
        raise ValueError("No JSON object found")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(s)):
        ch = s[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return s[start : i + 1]
    raise ValueError("Unclosed JSON object")


def _parse_creator_json(text: str) -> Dict[str, Any]:
    payload = _extract_first_json_object(text)
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Creator JSON must be an object")
    draft_text = data.get("draft_text")
    self_check = data.get("self_check", [])
    if not isinstance(draft_text, str):
        raise ValueError("draft_text must be string")
    if not isinstance(self_check, list) or not all(isinstance(x, str) for x in self_check):
        raise ValueError("self_check must be string[]")
    return {"draft_text": draft_text.strip(), "self_check": self_check}


def _fallback_creator(
    user_text: str,
    guide: Dict[str, Any],
    *,
    prev_draft: Optional[str],
    notes: List[str],
) -> Dict[str, Any]:
    constraints = (guide or {}).get("constraints") or {}
    style = constraints.get("style") or "写实电影感"
    tone = constraints.get("tone") or "克制"
    setting = constraints.get("setting") or "未指定"
    header = f"风格：{style}；氛围：{tone}；设定：{setting}。"
    base = prev_draft.strip() if prev_draft else user_text.strip()
    # 简单把优化意见拼到自检里，便于观察迭代
    sc = ["fallback：未启用或调用 LLM 失败，使用拼接策略生成草稿。"]
    sc += [f"采纳优化意见：{n}" for n in notes[:5]]
    draft = f"{header}\n\n{base}"
    return {"draft_text": draft.strip(), "self_check": sc}
