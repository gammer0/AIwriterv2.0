import os
import unittest
from pathlib import Path

from workflows.pipeline import _safe_write_text


class TestYamlOutPath(unittest.TestCase):
    def test_safe_write_text_writes_relative(self) -> None:
        # ensure under repo and cleanup afterwards
        out = Path("outputs") / "test_storyboard.yaml"
        try:
            p = _safe_write_text(out, "a: 1\n")
            self.assertEqual(p, "outputs/test_storyboard.yaml")
            self.assertTrue((Path.cwd() / out).exists())
        finally:
            try:
                (Path.cwd() / out).unlink()
            except FileNotFoundError:
                pass
            try:
                (Path.cwd() / "outputs").rmdir()
            except OSError:
                pass

    def test_safe_write_text_blocks_escape(self) -> None:
        # try escaping repo root
        with self.assertRaises(ValueError):
            _safe_write_text(Path("..") / "x.yaml", "a: 1\n")


if __name__ == "__main__":
    unittest.main()

