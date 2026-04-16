from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import Agent, AgentResult
from app.settings import get_settings
from llm.client import LLMClient


class SemanticSplitAgent(Agent):
    name = "semantic_split"

    def run(self, text: str, **kwargs: object) -> AgentResult:
        cleaned = re.sub(r"\s+", " ", text.strip())
        if not cleaned:
            return AgentResult(data={"scenes": []})

        settings = get_settings()
        system_prompt = _load_system_prompt(Path("prompts") / "语义分割agent.md")

        scenes: Optional[List[str]] = None
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
                resp = client.chat(cleaned, system=system_prompt)
                raw = resp.raw
                scenes = _parse_scenes_json(resp.text)
            except Exception as e:
                llm_error = str(e)

        if scenes is None:
            scenes = _fallback_split(cleaned)

        return AgentResult(
            data={
                "scenes": scenes,
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


def _parse_scenes_json(text: str) -> List[str]:
    payload = _extract_first_json_object(text)
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Semantic split JSON must be an object")
    scenes = data.get("scenes")
    if not isinstance(scenes, list) or not scenes or not all(isinstance(x, str) for x in scenes):
        raise ValueError("scenes must be non-empty string[]")
    return [s.strip() for s in scenes if s.strip()]


def _fallback_split(cleaned: str) -> List[str]:
    chunks: List[str] = []
    buf: List[str] = []
    for part in re.split(r"([。！？；.!?;])", cleaned):
        if not part:
            continue
        buf.append(part)
        if part in "。！？；.!?;":
            chunk = "".join(buf).strip()
            buf = []
            if chunk:
                chunks.append(chunk)
    if buf:
        chunk = "".join(buf).strip()
        if chunk:
            chunks.append(chunk)

    scenes: List[str] = []
    max_len = 80
    for c in chunks:
        if len(c) <= max_len:
            scenes.append(c)
            continue
        for i in range(0, len(c), max_len):
            s = c[i : i + max_len].strip()
            if s:
                scenes.append(s)

    return scenes or [cleaned]
