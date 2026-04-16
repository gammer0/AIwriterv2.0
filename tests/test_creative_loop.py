import unittest

from workflows.creative_loop import run_creative_loop


class TestCreativeLoop(unittest.TestCase):
    def test_iterations_records_length(self) -> None:
        guide = {
            "summary": "x",
            "tips": ["a"],
            "constraints": {"style": "写实", "tone": "平静", "setting": "城市", "protagonists": [], "do_not": []},
        }
        out = run_creative_loop("原始文本", guide=guide, iterations=3)
        self.assertEqual(out["iterations"], 3)
        self.assertEqual(len(out["records"]), 3)
        self.assertIsInstance(out["final_text"], str)


if __name__ == "__main__":
    unittest.main()

