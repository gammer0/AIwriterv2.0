from __future__ import annotations

from typing import Any, Dict

from agents.consistency_guard import ConsistencyGuardAgent
from agents.creative_guide import CreativeGuideAgent
from agents.semantic_split import SemanticSplitAgent
from agents.storyboard_prompt import StoryboardPromptAgent
from workflows.creative_loop import run_creative_loop


def run_workflow(text: str, *, iterations: int = 1) -> Dict[str, Any]:
    guide = CreativeGuideAgent().run(text).data

    loop = run_creative_loop(text, guide=guide.get("guide", {}), iterations=iterations)
    final_text = loop.get("final_text", "").strip()

    scenes = SemanticSplitAgent().run(final_text).data.get("scenes", [])
    consistency = ConsistencyGuardAgent().run(text, scenes=scenes).data.get("consistency", {})
    storyboard = StoryboardPromptAgent().run(scenes=scenes, consistency=consistency).data

    return {
        "scenes": storyboard.get("scenes", []),
        "consistency_notes": consistency,
        "meta": {
            "agents": {
                "guide": guide.get("guide", {}),
                "creative_loop": loop,
            }
        },
    }
