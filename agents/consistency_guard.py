from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import Agent, AgentResult
from app.settings import get_settings
from llm.client import LLMClient


class ConsistencyGuardAgent(Agent):
    name = "consistency_guard"

    def run(self, text: str, scenes: List[str] | None = None, **kwargs: object) -> AgentResult:
        scenes = scenes or []
        settings = get_settings()
        system_prompt = _load_system_prompt(Path("prompts") / "场景一致性监督agent.md")

        consistency: Optional[Dict[str, Any]] = None
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
                payload = json.dumps({"text": text, "scenes": scenes}, ensure_ascii=False)
                resp = client.chat(payload, system=system_prompt)
                raw = resp.raw
                consistency = _parse_consistency_json(resp.text)
            except Exception as e:
                llm_error = str(e)

        if consistency is None:
            consistency = _fallback_consistency(text, scenes)

        return AgentResult(
            data={
                "consistency": consistency,
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


def _parse_consistency_json(text: str) -> Dict[str, Any]:
    payload = _extract_first_json_object(text)
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Consistency JSON must be an object")
    entities = data.get("entities")
    rules = data.get("rules")
    if not isinstance(entities, list) or not entities:
        raise ValueError("entities must be non-empty list")
    if not isinstance(rules, list) or not rules or not all(isinstance(x, str) for x in rules):
        raise ValueError("rules must be non-empty string[]")

    norm_entities: List[Dict[str, Any]] = []
    for e in entities:
        if not isinstance(e, dict):
            continue
        t = e.get("text")
        attrs = e.get("attrs", [])
        if not isinstance(t, str) or not t.strip():
            continue
        if not isinstance(attrs, list) or not all(isinstance(x, str) for x in attrs):
            attrs = []
        norm_entities.append({"text": t.strip(), "attrs": [a.strip() for a in attrs if a.strip()]})

    if not norm_entities:
        raise ValueError("entities must contain at least one valid entity")

    return {"entities": norm_entities, "rules": [r.strip() for r in rules if r.strip()]}


def _fallback_consistency(text: str, scenes: List[str]) -> Dict[str, Any]:
    full = " ".join([text] + scenes)
    candidates = re.findall(r"[\u4e00-\u9fff]{2,6}", full)
    freq: Dict[str, int] = {}
    for w in candidates:
        freq[w] = freq.get(w, 0) + 1
    top = [w for w, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:8]]

    entities = [{"text": w, "attrs": []} for w in top] or [{"text": "主体", "attrs": []}]
    rules = [
        "人物外观、服装与身份设定跨分镜保持一致（仅允许角度/姿态/光线变化）。",
        "关键道具（如手机、武器、包等）不得无故消失或突变形态/颜色。",
        "地点关键特征（标志物、建筑风格、室内布局）保持一致，转场需明确。",
        "同一主体的称呼保持一致，避免出现多个不明同名主体。",
    ]
    return {"entities": entities, "rules": rules}
