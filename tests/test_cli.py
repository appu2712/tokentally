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


if __name__ == "__main__":
    unittest.main()
