import unittest

from agents.storyboard_prompt import render_yaml


class TestStoryboardYaml(unittest.TestCase):
    def test_render_yaml_has_sections(self) -> None:
        data = {
            "global_constraints": {"entities": [], "rules": ["r"], "style": "s", "negative": []},
            "scenes": [{"index": 1, "text": "t", "prompt": "p", "negative": []}],
        }
        y = render_yaml(data)
        self.assertIn("global_constraints:", y)
        self.assertIn("scenes:", y)


if __name__ == "__main__":
    unittest.main()

