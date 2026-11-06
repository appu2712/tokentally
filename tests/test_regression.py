import unittest
from tokentally.regression import compare_prompt_regression, RegressionComparator


class TestRegression(unittest.TestCase):
    def test_regression_detected(self):
        baseline = "Short system instruction for prompt testing."
        candidate = baseline + " Extra lengthy guidelines added here that bloat the context size significantly."
        res = compare_prompt_regression(baseline, candidate, max_regression_pct=10.0)

        self.assertTrue(res.is_regression)
        self.assertTrue(res.is_violation)
        self.assertGreater(res.delta_tokens, 0)
        self.assertGreater(res.projected_monthly_impact_10k_usd, 0)

    def test_no_regression_when_within_threshold(self):
        baseline = "System instruction with reasonable baseline content."
        candidate = "System instruction with reasonable baseline content."
        res = compare_prompt_regression(baseline, candidate, max_regression_pct=15.0)

        self.assertFalse(res.is_regression)
        self.assertFalse(res.is_violation)
        self.assertEqual(res.delta_tokens, 0)


if __name__ == "__main__":
    unittest.main()
