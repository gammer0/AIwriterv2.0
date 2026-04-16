import unittest

from agents.creative_guide import _extract_first_json_object, _parse_guide_json


class TestCreativeGuideParsing(unittest.TestCase):
    def test_extract_from_code_fence(self) -> None:
        s = "```json\n{\"summary\":\"a\",\"tips\":[\"t\"],\"constraints\":{}}\n```"
        self.assertEqual(_extract_first_json_object(s), "{\"summary\":\"a\",\"tips\":[\"t\"],\"constraints\":{}}")

    def test_parse_normalizes_constraints(self) -> None:
        data = _parse_guide_json(
            "{\"summary\":\"a\",\"tips\":[\"t\"],\"constraints\":{\"style\":\"s\",\"tone\":\"t\",\"setting\":\"x\"}}"
        )
        self.assertIn("constraints", data)
        self.assertIn("protagonists", data["constraints"])
        self.assertIn("do_not", data["constraints"])


if __name__ == "__main__":
    unittest.main()

