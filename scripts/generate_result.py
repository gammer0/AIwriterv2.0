from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_repo_root_on_syspath() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def main() -> int:
    _ensure_repo_root_on_syspath()
    from workflows.pipeline import run_workflow

    parser = argparse.ArgumentParser(description="Run workflow once and produce final script + storyboard YAML.")
    parser.add_argument("--text", type=str, default=None, help="Input text (if omitted, use --text-file).")
    parser.add_argument("--text-file", type=str, default=None, help="UTF-8 text file path.")
    parser.add_argument("--iterations", type=int, default=2, help="Creative loop iterations (1-10).")
    parser.add_argument("--yaml-out", type=str, default="storyboard.yaml", help="Output YAML path under repo root.")
    args = parser.parse_args()

    if args.text is None and args.text_file is None:
        parser.error("one of --text or --text-file is required")

    if args.text_file:
        text = Path(args.text_file).read_text(encoding="utf-8").strip()
    else:
        text = (args.text or "").strip()

    result = run_workflow(text, iterations=args.iterations, yaml_out=args.yaml_out)

    loop = (((result or {}).get("meta") or {}).get("agents") or {}).get("creative_loop") or {}
    final_text = loop.get("final_text") or ""
    yaml_path = (((result or {}).get("meta") or {}).get("agents") or {}).get("storyboard_yaml_path") or args.yaml_out

    print("== Final Text ==")
    print(final_text)
    print()
    print(f"== YAML Written ==\n{yaml_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

