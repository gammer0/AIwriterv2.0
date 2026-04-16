import unittest

from agents.consistency_guard import _fallback_consistency, _parse_consistency_json


class TestConsistencyGuardParsing(unittest.TestCase):
    def test_parse_json(self) -> None:
        out = _parse_consistency_json(
            '{"entities":[{"text":"女孩","attrs":["黑色短发"]}],"rules":["保持一致"]}'
        )
        self.assertIn("entities", out)
        self.assertIn("rules", out)
        self.assertEqual(out["entities"][0]["text"], "女孩")

    def test_parse_json_from_fence(self) -> None:
        out = _parse_consistency_json(
            '```json\n{"entities":[{"text":"A","attrs":[]}],"rules":["r"]}\n```'
        )
        self.assertEqual(out["entities"][0]["text"], "A")

    def test_fallback_shape(self) -> None:
        out = _fallback_consistency("一个女孩。", ["她走进房间。"])
        self.assertTrue(len(out["entities"]) >= 1)
        self.assertTrue(len(out["rules"]) >= 1)


if __name__ == "__main__":
    unittest.main()

