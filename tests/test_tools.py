import json
import unittest
from tokentally.tools import (
    analyze_tool_schemas,
    simulate_history_growth,
    ToolWorkloadEngine,
)


class TestTools(unittest.TestCase):
    def test_analyze_tool_schemas(self):
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Fetch current weather conditions for a given city location.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string", "description": "City and country"},
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        rep = analyze_tool_schemas(json.dumps(tools))
        self.assertEqual(rep.total_tools, 1)
        self.assertGreater(rep.total_tokens, 0)
        self.assertEqual(rep.tools[0].name, "get_weather")
        self.assertEqual(rep.tools[0].field_count, 2)

    def test_simulate_history_growth(self):
        res = simulate_history_growth(num_turns=5, tokens_per_turn=200, model="gpt-4o")
        self.assertEqual(res.num_turns, 5)
        self.assertEqual(res.final_turn_context_tokens, 1000)
        # Cumulative = 200 * (5 * 6 / 2) = 3000
        self.assertEqual(res.cumulative_processed_tokens, 3000)
        self.assertEqual(res.cumulative_overhead_multiplier, 3.0)

    def test_audit_agent_trace_loop_detection(self):
        engine = ToolWorkloadEngine()
        steps = [
            {"tool": "web_search", "args": {"query": "python decorators"}},
            {"tool": "web_search", "args": {"query": "python decorators"}},
            {"tool": "web_search", "args": {"query": "python decorators"}},
        ]
        audit = engine.audit_agent_trace(steps)
        self.assertTrue(audit.loop_detected)
        self.assertEqual(audit.duplicate_calls, 2)
        self.assertLess(audit.progress_per_token_score, 0.5)


if __name__ == "__main__":
    unittest.main()
