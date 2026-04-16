from __future__ import annotations

import re
from typing import Dict, List

from agents.base import Agent, AgentResult


class ConsistencyGuardAgent(Agent):
    name = "consistency_guard"

    def run(self, text: str, scenes: List[str] | None = None, **kwargs: object) -> AgentResult:
        scenes = scenes or []
        full = " ".join([text] + scenes)
        # 极简提取：抓一些可能需要一致性的名词（骨架版）
        candidates = re.findall(r"[\u4e00-\u9fff]{2,6}", full)
        freq: Dict[str, int] = {}
        for w in candidates:
            freq[w] = freq.get(w, 0) + 1
        top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return AgentResult(
            data={
                "consistency": {
                    "entities": [{"text": w, "count": c} for w, c in top],
                    "note": "骨架版：仅做粗略实体提示，后续可接入 LLM/规则增强。",
                }
            }
        )
