from __future__ import annotations

from agents.base import Agent, AgentResult


class CreativeRefineAgent(Agent):
    name = "creative_refine"

    def run(self, text: str, **kwargs: object) -> AgentResult:
        refined = text.strip()
        return AgentResult(
            data={
                "refined_text": refined,
                "refine_notes": ["保留原文（当前为骨架实现）"],
            }
        )
