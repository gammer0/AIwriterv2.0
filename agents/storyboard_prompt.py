from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from agents.base import Agent, AgentResult
from app.settings import get_settings
from llm.client import LLMClient


class StoryboardPromptAgent(Agent):
    name = "storyboard_prompt"

    def run(
        self,
        scenes: List[str],
        consistency: Dict[str, object] | None = None,
        **kwargs: object,
    ) -> AgentResult:
        consistency = consistency or {}
        settings = get_settings()
        system_prompt = _load_system_prompt(Path("prompts") / "多分镜通用提示词agent.md")

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
                payload = json.dumps({"scenes": scenes, "consistency": consistency}, ensure_ascii=False)
                resp = client.chat(payload, system=system_prompt)
                raw = resp.raw
                result = _parse_storyboard_json(resp.text, expected_len=len(scenes))
            except Exception as e:
                llm_error = str(e)

        if result is None:
            result = _fallback_storyboard(scenes, consistency)

        yaml_text = render_yaml(result)
        return AgentResult(
            data={
                "yaml": yaml_text,
                "data": result,
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


def _parse_storyboard_json(text: str, *, expected_len: int) -> Dict[str, Any]:
    payload = _extract_first_json_object(text)
    data = json.loads(payload)
    if not isinstance(data, dict):
        raise ValueError("Storyboard JSON must be an object")

    gc = data.get("global_constraints")
    scenes = data.get("scenes")
    if not isinstance(gc, dict):
        raise ValueError("global_constraints must be object")
    if not isinstance(scenes, list) or len(scenes) != expected_len:
        raise ValueError("scenes must be array with same length as input scenes")

    # normalize global_constraints
    gc_entities = gc.get("entities") if isinstance(gc.get("entities"), list) else []
    gc_rules = gc.get("rules") if isinstance(gc.get("rules"), list) else []
    gc_style = gc.get("style") if isinstance(gc.get("style"), str) else ""
    gc_negative = gc.get("negative") if isinstance(gc.get("negative"), list) else []
    if not all(isinstance(x, str) for x in gc_rules):
        raise ValueError("global_constraints.rules must be string[]")
    if gc_negative and not all(isinstance(x, str) for x in gc_negative):
        raise ValueError("global_constraints.negative must be string[]")

    norm_gc_entities: List[Dict[str, Any]] = []
    for e in gc_entities:
        if not isinstance(e, dict):
            continue
        t = e.get("text")
        attrs = e.get("attrs", [])
        if not isinstance(t, str) or not t.strip():
            continue
        if not isinstance(attrs, list) or not all(isinstance(x, str) for x in attrs):
            attrs = []
        norm_gc_entities.append({"text": t.strip(), "attrs": [a.strip() for a in attrs if a.strip()]})

    norm_scenes: List[Dict[str, Any]] = []
    for i, s in enumerate(scenes, start=1):
        if not isinstance(s, dict):
            raise ValueError("each scene must be object")
        idx = s.get("index")
        st = s.get("text")
        prompt = s.get("prompt")
        neg = s.get("negative", [])
        if idx != i:
            raise ValueError("scene.index must be 1..N in order")
        if not isinstance(st, str) or not isinstance(prompt, str):
            raise ValueError("scene.text and scene.prompt must be string")
        if neg is None:
            neg = []
        if not isinstance(neg, list) or not all(isinstance(x, str) for x in neg):
            raise ValueError("scene.negative must be string[]")
        norm_scenes.append({"index": i, "text": st.strip(), "prompt": prompt.strip(), "negative": [x.strip() for x in neg if x.strip()]})

    return {
        "global_constraints": {
            "entities": norm_gc_entities,
            "rules": [r.strip() for r in gc_rules if isinstance(r, str) and r.strip()],
            "style": gc_style.strip(),
            "negative": [n.strip() for n in gc_negative if isinstance(n, str) and n.strip()],
        },
        "scenes": norm_scenes,
    }


def _fallback_storyboard(scenes: List[str], consistency: Dict[str, object]) -> Dict[str, Any]:
    entities = []
    rules = []
    style = "写实电影感"
    negative = ["低清", "模糊", "畸形肢体", "多余手指"]

    if isinstance(consistency, dict):
        ent = consistency.get("entities")
        r = consistency.get("rules")
        if isinstance(ent, list):
            for e in ent[:10]:
                if isinstance(e, dict) and isinstance(e.get("text"), str):
                    attrs = e.get("attrs", [])
                    if not isinstance(attrs, list) or not all(isinstance(x, str) for x in attrs):
                        attrs = []
                    entities.append({"text": e["text"], "attrs": [x for x in attrs if x]})
        if isinstance(r, list) and all(isinstance(x, str) for x in r):
            rules = r[:10]

    entity_hint = ""
    if entities:
        entity_hint = "一致性元素：" + "、".join([e["text"] for e in entities[:5]])

    out_scenes: List[Dict[str, Any]] = []
    for i, s in enumerate(scenes, start=1):
        prompt = (
            f"分镜{i}：{s}\n"
            f"风格：{style}。\n"
            "镜头：写实电影感，稳定构图，清晰主体，合理景别与镜头运动。\n"
            "画面：主体、动作、环境、光线与氛围清晰可见。\n"
            f"{entity_hint}"
        ).strip()
        out_scenes.append({"index": i, "text": s, "prompt": prompt, "negative": []})

    return {
        "global_constraints": {"entities": entities, "rules": rules, "style": style, "negative": negative},
        "scenes": out_scenes,
    }


def render_yaml(data: Dict[str, Any]) -> str:
    """
    Minimal YAML renderer for the specific output shape:
      - dict / list / str / int / bool / None
    """
    return _yaml_dump(data).rstrip() + "\n"


def _yaml_dump(obj: Any, indent: int = 0) -> str:
    sp = "  " * indent
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if isinstance(obj, int):
        return str(obj)
    if isinstance(obj, str):
        return _yaml_quote(obj)
    if isinstance(obj, list):
        if not obj:
            return "[]"
        lines: List[str] = []
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{sp}- {_yaml_dump(item, indent + 1).lstrip()}")
            else:
                lines.append(f"{sp}- {_yaml_dump(item, 0)}")
        return "\n".join(lines)
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        lines = []
        for k, v in obj.items():
            key = str(k)
            if isinstance(v, (dict, list)):
                rendered = _yaml_dump(v, indent + 1)
                if "\n" in rendered:
                    lines.append(f"{sp}{key}:\n{rendered}")
                else:
                    lines.append(f"{sp}{key}: {rendered}")
            else:
                lines.append(f"{sp}{key}: {_yaml_dump(v, 0)}")
        return "\n".join(lines)
    return _yaml_quote(str(obj))


def _yaml_quote(s: str) -> str:
    if s == "":
        return "''"
    # Quote if contains risky chars/newlines
    if any(c in s for c in [":", "{", "}", "[", "]", "#", "\n", "\r", "\t"]):
        return "'" + s.replace("'", "''") + "'"
    if s.strip() != s:
        return "'" + s.replace("'", "''") + "'"
    return s
