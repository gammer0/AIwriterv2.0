from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional

from agents.base import Agent, AgentResult
from app.settings import get_settings
from llm.client import LLMClient


class CreativeGuideAgent(Agent):
    name = "creative_guide"

    def run(self, text: str, **kwargs: object) -> AgentResult:
        settings = get_settings()
        system_prompt = _load_system_prompt(Path("prompts") / "创作指导agent.md")

        guide: Optional[Dict[str, Any]] = None
        raw: Optional[Dict[str, Any]] = None
        llm_error: Optional[str] = None

        if settings.llm_relay_base_url and not settings.disable_llm:
            try:
                client = LLMClient.build(
                    base_url=settings.llm_relay_base_url,
                    api_key=settings.llm_relay_api_key,
                    model=settings.llm_model,
                    timeout_s=60.0,
                )
                resp = client.chat(text, system=system_prompt)
                raw = resp.raw
                guide = _parse_guide_json(resp.text)
            except Exception as e:
                llm_error = str(e)

        if guide is None:
            guide = _fallback_guide(text)

        return AgentResult(
            data={
                "guide": guide,
                "llm": {
                    "enabled": bool(settings.llm_relay_base_url) and not settings.disable_llm,
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


def _parse_guide_json(text: str) -> Dict[str, Any]:
    payload = _extract_first_json_object(text)
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Guide JSON must be an object")

    summary = data.get("summary")
    tips = data.get("tips")
    constraints = data.get("constraints")
    if not isinstance(summary, str):
        raise ValueError("summary must be string")
    if not isinstance(tips, list) or not all(isinstance(x, str) for x in tips):
        raise ValueError("tips must be string[]")
    if not isinstance(constraints, dict):
        raise ValueError("constraints must be object")

    for k in ("style", "tone", "setting"):
        if k in constraints and constraints[k] is not None and not isinstance(constraints[k], str):
            raise ValueError(f"constraints.{k} must be string")
    for k in ("protagonists", "do_not"):
        if k in constraints and constraints[k] is not None:
            v = constraints[k]
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                raise ValueError(f"constraints.{k} must be string[]")

    # Normalize missing keys
    constraints.setdefault("style", "")
    constraints.setdefault("tone", "")
    constraints.setdefault("setting", "")
    constraints.setdefault("protagonists", [])
    constraints.setdefault("do_not", [])
    data["constraints"] = constraints
    return data


def _extract_first_json_object(s: str) -> str:
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return s
    # common bad outputs: ```json ... ```
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


def _fallback_guide(text: str) -> Dict[str, Any]:
    tips = [
        "明确主角/场景/时间与情绪基调（信息不足可先设定默认）",
        "把抽象情绪改成可拍细节：光线、天气、镜头、动作、材质",
        "把一段多事件拆成多个短场景，每镜尽量只做一件事",
    ]
    return {
        "summary": "创作指导（fallback）",
        "tips": tips,
        "constraints": {
            "style": "写实电影感",
            "tone": "根据文本推断",
            "setting": "未指定",
            "protagonists": [],
            "do_not": [],
        },
    }
