import tempfile
import unittest
from pathlib import Path
from tokentally.config import load_config, _parse_simple_toml


class TestConfig(unittest.TestCase):
    def test_simple_toml_parser(self):
        content = """
        [budget]
        max_prompt_tokens = 50000
        max_cost_per_request = 0.25
        warning_cost_usd = 0.15
        default_model = "gpt-4o"

        [regression]
        max_regression_pct = 12.5
        fail_on_regression = true
        """
        raw = _parse_simple_toml(content)
        self.assertEqual(raw["budget"]["max_prompt_tokens"], 50000)
        self.assertEqual(raw["budget"]["max_cost_per_request"], 0.25)
        self.assertEqual(raw["regression"]["max_regression_pct"], 12.5)
        self.assertEqual(raw["regression"]["fail_on_regression"], True)

    def test_load_config_from_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cfg_file = Path(tmpdir) / "tokentally.toml"
            cfg_file.write_text("""
            [budget]
            max_prompt_tokens = 8000
            max_cost_per_request = 0.05
            """, encoding="utf-8")

            cfg = load_config(tmpdir)
            self.assertEqual(cfg.budget.max_prompt_tokens, 8000)
            self.assertEqual(cfg.budget.max_cost_per_request, 0.05)


if __name__ == "__main__":
    unittest.main()
