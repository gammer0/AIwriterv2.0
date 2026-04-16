from __future__ import annotations

from typing import Dict, List

from agents.base import Agent, AgentResult


class StoryboardPromptAgent(Agent):
    name = "storyboard_prompt"

    def run(
        self,
        scenes: List[str],
        consistency: Dict[str, object] | None = None,
        **kwargs: object,
    ) -> AgentResult:
        consistency = consistency or {}
        entities = consistency.get("entities") or []
        entity_hint = ""
        if isinstance(entities, list) and entities:
            entity_hint = "保持一致性元素：" + "、".join(
                [str(e.get("text")) for e in entities[:5] if isinstance(e, dict) and e.get("text")]
            )

        prompts: List[Dict[str, object]] = []
        for i, s in enumerate(scenes, start=1):
            prompt = f"分镜{i}：{s}\n镜头：写实电影感，稳定构图，清晰主体。\n{entity_hint}".strip()
            prompts.append({"index": i, "text": s, "prompt": prompt})

        return AgentResult(data={"scenes": prompts})
