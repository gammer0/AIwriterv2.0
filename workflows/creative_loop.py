from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from agents.creator import CreatorAgent
from agents.optimizer import OptimizerAgent


@dataclass(frozen=True)
class IterationRecord:
    iteration: int
    draft_text: str
    creator_self_check: List[str]
    optimizer_notes: List[str]
    optimizer_risk: List[str]


def run_creative_loop(
    user_text: str,
    *,
    guide: Dict[str, Any],
    iterations: int = 1,
) -> Dict[str, Any]:
    """
    iterations:
      - 1: 仅创作一次（无优化回路）
      - >=2: 创作 -> 优化 -> 再创作 ...（总共创作 iterations 次，优化 iterations-1 次）
    """
    iters = max(1, int(iterations))
    creator = CreatorAgent()
    optimizer = OptimizerAgent()

    records: List[IterationRecord] = []
    prev_draft: Optional[str] = None
    notes: List[str] = []

    for i in range(1, iters + 1):
        c = creator.run(user_text, guide=guide, prev_draft=prev_draft, notes=notes).data
        draft_text = str(c.get("draft_text", "")).strip()
        self_check = c.get("self_check") if isinstance(c.get("self_check"), list) else []

        opt_notes: List[str] = []
        opt_risk: List[str] = []
        if i < iters:
            history = [
                {
                    "iteration": r.iteration,
                    "draft_text": r.draft_text,
                    "optimizer_notes": r.optimizer_notes,
                }
                for r in records
            ]
            o = optimizer.run(guide=guide, draft_text=draft_text, history=history).data
            opt_notes = o.get("notes") if isinstance(o.get("notes"), list) else []
            opt_risk = o.get("risk") if isinstance(o.get("risk"), list) else []
            notes = [str(x) for x in opt_notes if isinstance(x, str)]

        records.append(
            IterationRecord(
                iteration=i,
                draft_text=draft_text,
                creator_self_check=[str(x) for x in self_check if isinstance(x, str)],
                optimizer_notes=[str(x) for x in opt_notes if isinstance(x, str)],
                optimizer_risk=[str(x) for x in opt_risk if isinstance(x, str)],
            )
        )
        prev_draft = draft_text

    final_text = records[-1].draft_text if records else user_text.strip()
    return {
        "final_text": final_text,
        "iterations": iters,
        "records": [r.__dict__ for r in records],
    }

