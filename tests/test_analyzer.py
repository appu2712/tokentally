import json
import unittest
from tokentally.analyzer import analyze_prompt_context, PromptContextAnalyzer


class TestAnalyzer(unittest.TestCase):
    def test_analyze_chat_json_messages(self):
        chat_data = [
            {"role": "system", "content": "You are a helpful coding assistant. Follow clean architecture."},
            {"role": "user", "content": "How do I reverse a linked list in Python?"},
            {"role": "assistant", "content": "Here is how to reverse a linked list..."},
            {"role": "user", "content": "Can you do it iteratively?"}
        ]
        chat_str = json.dumps(chat_data)
        res = analyze_prompt_context(chat_str, model="gpt-4o")

        self.assertGreater(res.total_tokens, 0)
        layer_names = [c.name for c in res.components]
        self.assertIn("system_instructions", layer_names)
        self.assertIn("conversation_history", layer_names)
        self.assertIn("user_request", layer_names)

    def test_cacheability_breaker_detection(self):
        prompt_with_timestamp = "Request timestamp: 2026-11-06T15:30:00. You are a weather bot."
        res = analyze_prompt_context(prompt_with_timestamp, model="gpt-4o")
        self.assertFalse(res.cacheability.cache_eligible)
        self.assertTrue(len(res.cacheability.cache_breaking_items) > 0)
        self.assertIn("ISO Timestamp", res.cacheability.cache_breaking_items)

    def test_reasoning_model_detection(self):
        res_o1 = analyze_prompt_context("Complex physics simulation question", model="o1")
        self.assertTrue(res_o1.reasoning_estimate.is_reasoning_model)
        self.assertGreater(res_o1.reasoning_estimate.estimated_reasoning_tokens_low, 0)

        res_4o = analyze_prompt_context("Simple question", model="gpt-4o")
        self.assertFalse(res_4o.reasoning_estimate.is_reasoning_model)


if __name__ == "__main__":
    unittest.main()
