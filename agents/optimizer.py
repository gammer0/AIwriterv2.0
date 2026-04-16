from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import Agent, AgentResult
from app.settings import get_settings
from llm.client import LLMClient


class OptimizerAgent(Agent):
    name = "optimizer"

    def run(
        self,
        *,
        guide: Dict[str, Any],
        draft_text: str,
        history: Optional[List[Dict[str, Any]]] = None,
        **kwargs: object,
    ) -> AgentResult:
        settings = get_settings()
        system_prompt = _load_system_prompt(Path("prompts") / "优化agent.md")

        payload = {
            "guide": guide,
            "draft_text": draft_text,
            "history": history or [],
        }

        result: Optional[Dict[str, Any]] = None
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
                resp = client.chat(json.dumps(payload, ensure_ascii=False), system=system_prompt)
                raw = resp.raw
                result = _parse_optimizer_json(resp.text)
            except Exception as e:
                llm_error = str(e)

        if result is None:
            result = _fallback_optimizer(guide, draft_text)

        return AgentResult(
            data={
                **result,
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


def _parse_optimizer_json(text: str) -> Dict[str, Any]:
    payload = _extract_first_json_object(text)
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Optimizer JSON must be an object")
    notes = data.get("notes", [])
    risk = data.get("risk", [])
    if not isinstance(notes, list) or not all(isinstance(x, str) for x in notes):
        raise ValueError("notes must be string[]")
    if not isinstance(risk, list) or not all(isinstance(x, str) for x in risk):
        raise ValueError("risk must be string[]")
    return {"notes": notes, "risk": risk}


def _fallback_optimizer(guide: Dict[str, Any], draft_text: str) -> Dict[str, Any]:
    constraints = (guide or {}).get("constraints") or {}
    do_not = constraints.get("do_not") or []
    notes: List[str] = []
    if do_not:
        notes.append(f"检查禁忌点：确保不出现 {('、'.join(do_not[:5]))} 等内容。")
    notes += [
        "补全镜头可视化细节：光线/天气/材质/镜头运动/主体动作。",
        "减少一段多事件：把跳转/转折拆分为更清晰的段落。",
        "统一主角稳定特征（外观/服饰/身份）与场景关键特征。",
    ]
    return {"notes": notes[:8], "risk": ["fallback：未启用或调用 LLM 失败，使用规则化建议。"]}
