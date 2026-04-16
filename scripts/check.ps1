$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$env:DISABLE_LLM = "1"

Write-Host "==> Python syntax check (py_compile)"
python -m py_compile `
  app\main.py `
  app\routes.py `
  app\settings.py `
  workflows\pipeline.py `
  workflows\creative_loop.py `
  agents\base.py `
  agents\creative_guide.py `
  agents\creative_refine.py `
  agents\semantic_split.py `
  agents\consistency_guard.py `
  agents\storyboard_prompt.py `
  agents\creator.py `
  agents\optimizer.py `
  agents\storyboard_prompt.py `
  llm\relay_proxy.py `
  llm\client.py `
  scripts\llm_smoke_test.py

Write-Host "==> Unit tests (unittest discover)"
python -m unittest discover -s tests -p "test_*.py" -v

Write-Host "==> OK"
