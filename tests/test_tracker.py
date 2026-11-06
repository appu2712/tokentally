import unittest
from tokentally.tracker import BudgetTracker, BudgetExceededError, track


class TestTracker(unittest.TestCase):
    def test_budget_tracker_records(self):
        with BudgetTracker(max_budget_usd=10.0, name="test_run") as tracker:
            res1 = tracker.record("Hello world", completion="Greetings human", model="gpt-4o")
            res2 = tracker.record("Second prompt", completion="Second response", model="gpt-4o-mini")

        self.assertEqual(tracker.call_count, 2)
        self.assertGreater(tracker.total_cost_usd, 0)
        self.assertGreater(tracker.total_tokens, 0)
        summary = tracker.summary()
        self.assertEqual(summary["total_calls"], 2)

    def test_budget_tracker_exceeds(self):
        with self.assertRaises(BudgetExceededError):
            with BudgetTracker(max_budget_usd=0.00000001) as tracker:
                tracker.record("Massive prompt " * 100, model="gpt-4o")

    def test_decorator_track(self):
        @track(model="gpt-4o", max_cost_usd=1.00)
        def generate_response():
            return "This is a clean generation response."

        res = generate_response()
        self.assertEqual(res, "This is a clean generation response.")

        @track(model="gpt-4o", max_cost_usd=0.00000001)
        def expensive_call():
            return "Very long output text " * 100

        with self.assertRaises(BudgetExceededError):
            expensive_call()


if __name__ == "__main__":
    unittest.main()
