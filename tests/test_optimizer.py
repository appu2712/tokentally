import unittest
from tokentally.optimizer import optimize_prompt, PromptOptimizer


class TestOptimizer(unittest.TestCase):
    def test_optimize_empty(self):
        res = optimize_prompt("")
        self.assertEqual(res.original_tokens, 0)
        self.assertEqual(res.optimized_tokens, 0)

    def test_optimize_whitespace_and_newlines(self):
        raw = "Line 1" + "    " * 40 + "\n\n\n\nLine 2" + "    " * 40 + "\n\n\nLine 3"
        res = optimize_prompt(raw, max_consecutive_newlines=1)
        self.assertLess(res.optimized_length, res.original_length)
        self.assertIn("Line 1\nLine 2\nLine 3", res.optimized_text)

    def test_strip_comments(self):
        code = "def add(a, b):\n    # This is a comment\n    return a + b"
        res = optimize_prompt(code, strip_comments=True)
        self.assertNotIn("# This is a comment", res.optimized_text)
        self.assertIn("def add(a, b):", res.optimized_text)


if __name__ == "__main__":
    unittest.main()
