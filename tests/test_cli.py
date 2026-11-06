import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr

from tokentally.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_help(self):
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                ret = main(["--help"])
            except SystemExit as e:
                ret = e.code
        self.assertEqual(ret, 0)
        self.assertIn("tokentally", f.getvalue())

    def test_cli_models(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["models", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn("gpt-4o", f.getvalue())

    def test_cli_count(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["count", "Hello world from tokentally", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"tokens"', f.getvalue())

    def test_cli_cost(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["cost", "Hello world", "--model", "gpt-4o", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"total_cost_usd"', f.getvalue())

    def test_cli_check_pass(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["check", "Hello world", "--max-cost", "1.0", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"passed": true', f.getvalue())

    def test_cli_check_fail(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["check", "Hello world", "--max-tokens", "1", "--json"])
        self.assertEqual(ret, 1)
        self.assertIn('"passed": false', f.getvalue())

    def test_cli_analyze(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["analyze", "# System\nYou are a bot.\n\n# User\nHello", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"components"', f.getvalue())
        self.assertIn('"cacheability"', f.getvalue())

    def test_cli_regression(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["regression", "base prompt", "candidate prompt with more text", "--json"])
        self.assertIn('"delta_tokens"', f.getvalue())

    def test_cli_history(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["history", "--turns", "5", "--tokens-per-turn", "100", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"cumulative_overhead_multiplier"', f.getvalue())

    def test_cli_trace(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["trace", '[{"tool": "calc", "args": {"x": 1}}, {"tool": "calc", "args": {"x": 1}}]', "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"progress_per_token_score"', f.getvalue())

    def test_cli_file_not_found(self):
        f_err = io.StringIO()
        with redirect_stderr(f_err):
            ret = main(["count", "nonexistent_file_xyz.txt"])
        self.assertEqual(ret, 1)
        self.assertIn("File not found", f_err.getvalue())

    def test_cli_file_not_found_json(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["count", "nonexistent_file_xyz.txt", "--json"])
        self.assertEqual(ret, 1)
        self.assertIn('"error"', f.getvalue())
        self.assertIn('"status": "failed"', f.getvalue())

    def test_cli_compare(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["compare", "Test prompt for comparison", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"total_cost_usd"', f.getvalue())

    def test_cli_optimize(self):
        f = io.StringIO()
        with redirect_stdout(f):
            ret = main(["optimize", "Line 1\n\n\n\nLine 2", "--json"])
        self.assertEqual(ret, 0)
        self.assertIn('"saved_tokens"', f.getvalue())

    def test_cli_models_add_and_remove(self):
        f_add = io.StringIO()
        with redirect_stdout(f_add):
            ret_add = main(["models", "--add", "test-finetune-cli", "--input", "0.75", "--output", "2.25", "--json"])
        self.assertEqual(ret_add, 0)
        self.assertIn('"status": "added"', f_add.getvalue())

        f_rem = io.StringIO()
        with redirect_stdout(f_rem):
            ret_rem = main(["models", "--remove", "test-finetune-cli", "--json"])
        self.assertEqual(ret_rem, 0)
        self.assertIn('"status": "removed"', f_rem.getvalue())


if __name__ == "__main__":
    unittest.main()
