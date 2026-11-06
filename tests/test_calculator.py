import unittest
from tokentally.calculator import estimate_cost, compare_models, CostCalculator
from tokentally.models import MODEL_REGISTRY, get_model_pricing


class TestCalculator(unittest.TestCase):
    def test_get_model_pricing(self):
        p = get_model_pricing("gpt-4o")
        self.assertEqual(p.provider, "OpenAI")
        self.assertEqual(p.input_per_m, 2.50)
        self.assertEqual(p.output_per_m, 10.00)
        self.assertEqual(p.cached_input_per_m, 1.25)

    def test_model_alias(self):
        p1 = get_model_pricing("4o")
        p2 = get_model_pricing("gpt-4o")
        self.assertEqual(p1.name, p2.name)

    def test_unknown_model_raises(self):
        with self.assertRaises(KeyError):
            get_model_pricing("nonexistent-future-model-9000")

    def test_estimate_cost(self):
        # 1,000,000 tokens for gpt-4o should be exactly $2.50 input, $10.00 output
        res = estimate_cost(1_000_000, model="gpt-4o", completion_tokens=1_000_000)
        self.assertEqual(res.input_cost_usd, 2.50)
        self.assertEqual(res.output_cost_usd, 10.00)
        self.assertEqual(res.total_cost_usd, 12.50)

    def test_estimate_cost_with_caching(self):
        # 1M tokens with 500k cached
        res = estimate_cost(1_000_000, model="gpt-4o", cached_tokens=500_000)
        # Billable input = 500k * 2.5/1M = 1.25
        # Cached input = 500k * 1.25/1M = 0.625
        # Total = 1.875
        self.assertAlmostEqual(res.total_cost_usd, 1.875, places=5)

    def test_compare_models(self):
        rows = compare_models(100_000, models=["gpt-4o", "gpt-4o-mini", "claude-3-5-haiku"])
        self.assertEqual(len(rows), 3)
        # Check that rows are sorted ascending by cost
        for i in range(len(rows) - 1):
            self.assertLessEqual(rows[i].total_cost_usd, rows[i+1].total_cost_usd)


if __name__ == "__main__":
    unittest.main()
