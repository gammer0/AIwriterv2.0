import unittest

from agents.semantic_split import _parse_scenes_json, _fallback_split


class TestSemanticSplitParsing(unittest.TestCase):
    def test_parse_json(self) -> None:
        scenes = _parse_scenes_json('{"scenes":["a","b"]}')
        self.assertEqual(scenes, ["a", "b"])

    def test_parse_json_from_fence(self) -> None:
        scenes = _parse_scenes_json('```json\n{"scenes":["a"]}\n```')
        self.assertEqual(scenes, ["a"])

    def test_fallback_non_empty(self) -> None:
        scenes = _fallback_split("一句话。第二句话。")
        self.assertTrue(len(scenes) >= 1)

    def test_fallback_short_text(self) -> None:
        scenes = _fallback_split("很短")
        self.assertEqual(scenes, ["很短"])


if __name__ == "__main__":
    unittest.main()

