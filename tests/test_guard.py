import unittest
from tokentally.guard import check_budget, BudgetGuard


class TestGuard(unittest.TestCase):
    def test_guard_passes_within_budget(self):
        res = check_budget("short prompt", model="gpt-4o", max_cost_usd=1.00, max_tokens=100)
        self.assertTrue(res.passed)
        self.assertEqual(res.exit_code, 0)
        self.assertEqual(len(res.violations), 0)

    def test_guard_fails_when_tokens_exceeded(self):
        text = "word " * 500
        res = check_budget(text, model="gpt-4o", max_tokens=50)
        self.assertFalse(res.passed)
        self.assertEqual(res.exit_code, 1)
        self.assertTrue(any("Token count violation" in v for v in res.violations))

    def test_guard_fails_when_cost_exceeded(self):
        text = "word " * 1000
        # $0.00000001 max cost will definitely fail
        res = check_budget(text, model="gpt-4o", max_cost_usd=0.0000001)
        self.assertFalse(res.passed)
        self.assertEqual(res.exit_code, 1)
        self.assertTrue(any("Cost limit violation" in v for v in res.violations))


if __name__ == "__main__":
    unittest.main()
