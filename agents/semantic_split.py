from __future__ import annotations

import re
from typing import List

from agents.base import Agent, AgentResult


class SemanticSplitAgent(Agent):
    name = "semantic_split"

    def run(self, text: str, **kwargs: object) -> AgentResult:
        cleaned = re.sub(r"\s+", " ", text.strip())
        if not cleaned:
            return AgentResult(data={"scenes": []})

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

        # 控制为“短场景”（骨架版）：过长则粗暴切片
        scenes: List[str] = []
        max_len = 80
        for c in chunks:
            if len(c) <= max_len:
                scenes.append(c)
                continue
            for i in range(0, len(c), max_len):
                scenes.append(c[i : i + max_len].strip())

        return AgentResult(data={"scenes": scenes})
