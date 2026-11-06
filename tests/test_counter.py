import os
import tempfile
import unittest

from tokentally.counter import TokenCounter, count_tokens, get_model_encoding


class TestCounter(unittest.TestCase):
    def test_get_model_encoding(self):
        self.assertEqual(get_model_encoding("gpt-4o"), "o200k_base")
        self.assertEqual(get_model_encoding("gpt-4-turbo"), "cl100k_base")
        self.assertEqual(get_model_encoding("unknown-model"), "cl100k_base")

    def test_count_empty_and_short(self):
        counter = TokenCounter(force_heuristic=True)
        self.assertEqual(counter.count(""), 0)
        self.assertEqual(counter.count("a"), 1)
        self.assertEqual(counter.count("hi"), 1)

    def test_heuristic_counting(self):
        counter = TokenCounter(force_heuristic=True)
        text = "The quick brown fox jumps over the lazy dog."
        cnt = counter.count(text)
        self.assertTrue(8 <= cnt <= 12)

    def test_count_tokens_file_and_string(self):
        with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as f:
            f.write("def calculate_sum(a, b):\n    return a + b\n")
            f_path = f.name

        try:
            cnt_file = count_tokens(f_path, is_file=True)
            self.assertGreater(cnt_file, 0)
            cnt_text = count_tokens("def calculate_sum(a, b):\n    return a + b\n")
            self.assertEqual(cnt_file, cnt_text)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)


if __name__ == "__main__":
    unittest.main()
