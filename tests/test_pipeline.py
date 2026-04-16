from workflows.pipeline import run_workflow


def test_run_workflow_returns_scenes() -> None:
    result = run_workflow("一个女孩在雨夜的霓虹街头奔跑。她回头看见追来的影子。")
    assert "scenes" in result
    assert isinstance(result["scenes"], list)

