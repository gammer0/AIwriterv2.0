from __future__ import annotations

from typing import Any, Dict

from agents.consistency_guard import ConsistencyGuardAgent
from agents.creative_guide import CreativeGuideAgent
from agents.creative_refine import CreativeRefineAgent
from agents.semantic_split import SemanticSplitAgent
from agents.storyboard_prompt import StoryboardPromptAgent


def run_workflow(text: str) -> Dict[str, Any]:
    guide = CreativeGuideAgent().run(text).data
    refined = CreativeRefineAgent().run(text).data
    scenes = SemanticSplitAgent().run(refined.get("refined_text", "")).data.get("scenes", [])
    consistency = ConsistencyGuardAgent().run(text, scenes=scenes).data.get("consistency", {})
    storyboard = StoryboardPromptAgent().run(scenes=scenes, consistency=consistency).data

    return {
        "scenes": storyboard.get("scenes", []),
        "consistency_notes": consistency,
        "meta": {
            "agents": {
                "guide": guide.get("guide", {}),
                "refine_notes": refined.get("refine_notes", []),
            }
        },
    }
