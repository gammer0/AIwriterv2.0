from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agents.consistency_guard import ConsistencyGuardAgent
from agents.creative_guide import CreativeGuideAgent
from agents.semantic_split import SemanticSplitAgent
from agents.storyboard_prompt import StoryboardPromptAgent
from workflows.creative_loop import run_creative_loop


def run_workflow(text: str, *, iterations: int = 1, yaml_out: str | None = None) -> Dict[str, Any]:
    guide = CreativeGuideAgent().run(text).data

    loop = run_creative_loop(text, guide=guide.get("guide", {}), iterations=iterations)
    final_text = loop.get("final_text", "").strip()

    scenes = SemanticSplitAgent().run(final_text).data.get("scenes", [])
    consistency = ConsistencyGuardAgent().run(text, scenes=scenes).data.get("consistency", {})
    storyboard = StoryboardPromptAgent().run(scenes=scenes, consistency=consistency).data

    yaml_text = storyboard.get("yaml", "") or ""
    yaml_written_path: str | None = None
    if yaml_out:
        yaml_written_path = _safe_write_text(Path(yaml_out), yaml_text)

    return {
        # 兼容旧结构：仍返回每镜 prompt 列表
        "scenes": (storyboard.get("data") or {}).get("scenes", []),
        "consistency_notes": consistency,
        "meta": {
            "agents": {
                "guide": guide.get("guide", {}),
                "creative_loop": loop,
                "storyboard_yaml": yaml_text,
                "storyboard_yaml_path": yaml_written_path,
                "storyboard": storyboard.get("data", {}),
            }
        },
    }


def _safe_write_text(rel_path: Path, content: str) -> str:
    """
    Write file within repo root only. Returns normalized posix-ish path string.
    """
    repo_root = Path.cwd().resolve()
    target = (repo_root / rel_path).resolve()
    if repo_root != target and repo_root not in target.parents:
        raise ValueError("yaml_out must be a relative path under the project directory")
    if target.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError("yaml_out must end with .yaml or .yml")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return str(target.relative_to(repo_root)).replace("\\", "/")
