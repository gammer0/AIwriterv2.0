from __future__ import annotations

from agents.base import Agent, AgentResult


class CreativeGuideAgent(Agent):
    name = "creative_guide"

    def run(self, text: str, **kwargs: object) -> AgentResult:
        tips = [
            "明确主角/场景/时间与情绪基调",
            "用可视化细节替代抽象词（光线、镜头、材质、动作）",
            "尽量避免一镜塞太多事件，拆成可拍的短场景",
        ]
        return AgentResult(
            data={
                "guide": {
                    "summary": "创作指导（骨架版）",
                    "tips": tips,
                }
            }
        )
