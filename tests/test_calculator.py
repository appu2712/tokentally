import unittest
from tokentally.calculator import estimate_cost, compare_models, CostCalculator
from tokentally.models import (
    MODEL_REGISTRY,
    get_model_pricing,
    normalize_model_name,
    save_custom_model,
    remove_custom_model,
    list_supported_models,
    ModelPricing,
)


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

    def test_normalize_model_name_date_and_provider_prefixes(self):
        self.assertEqual(normalize_model_name("claude-3-5-sonnet-20241022"), "claude-3-5-sonnet")
        self.assertEqual(normalize_model_name("anthropic/claude-3-5-sonnet"), "claude-3-5-sonnet")
        self.assertEqual(normalize_model_name("openai/gpt-4o-2024-08-06"), "gpt-4o")
        self.assertEqual(normalize_model_name("gemini-1.5-flash-002"), "gemini-1.5-flash")

    def test_multi_provider_coverage(self):
        # Cohere
        p_cohere = get_model_pricing("command-r")
        self.assertEqual(p_cohere.provider, "Cohere")
        # Bedrock
        p_bedrock = get_model_pricing("bedrock-nova-pro")
        self.assertEqual(p_bedrock.provider, "AWS Bedrock")
        # Cerebras
        p_cerebras = get_model_pricing("cerebras-llama-3.3-70b")
        self.assertEqual(p_cerebras.provider, "Cerebras")
        # Qwen
        p_qwen = get_model_pricing("qwen-2.5-coder-32b")
        self.assertEqual(p_qwen.provider, "Alibaba / Open")

    def test_latest_frontier_models_2025_2026(self):
        # OpenAI latest
        p_45 = get_model_pricing("gpt-4.5")
        self.assertEqual(p_45.input_per_m, 75.00)
        p_o3 = get_model_pricing("o3")
        self.assertEqual(p_o3.input_per_m, 10.00)
        p_o3_pro = get_model_pricing("o3-pro")
        self.assertEqual(p_o3_pro.input_per_m, 20.00)

        # Anthropic latest
        p_37 = get_model_pricing("claude-3-7-sonnet")
        self.assertEqual(p_37.input_per_m, 3.00)
        self.assertEqual(p_37.cached_input_per_m, 0.30)
        p_35_opus = get_model_pricing("claude-3-5-opus")
        self.assertEqual(p_35_opus.input_per_m, 15.00)

        # xAI Grok latest
        p_grok3 = get_model_pricing("grok-3")
        self.assertEqual(p_grok3.provider, "xAI")
        self.assertEqual(p_grok3.input_per_m, 3.00)
        p_grok3_mini = get_model_pricing("grok-3-mini")
        self.assertEqual(p_grok3_mini.input_per_m, 0.30)

        # Google Gemini latest
        p_gemini_thinking = get_model_pricing("gemini-2.0-flash-thinking")
        self.assertEqual(p_gemini_thinking.input_per_m, 0.10)
        p_gemini_pro2 = get_model_pricing("gemini-2.0-pro")
        self.assertEqual(p_gemini_pro2.input_per_m, 1.25)

        # Mistral latest
        p_saba = get_model_pricing("mistral-saba")
        self.assertEqual(p_saba.input_per_m, 0.20)
        p_pixtral = get_model_pricing("pixtral-large")
        self.assertEqual(p_pixtral.input_per_m, 2.00)

        # Meta LLaMA 3.2 Vision
        p_llama_vis = get_model_pricing("llama-3.2-90b-vision")
        self.assertEqual(p_llama_vis.input_per_m, 0.90)

    def test_list_models_filtering(self):
        grok_models = list_supported_models(search="grok")
        self.assertTrue(any("grok-3" in m for m in grok_models))

        openai_models = list_supported_models(provider="OpenAI")
        self.assertTrue(all(MODEL_REGISTRY[m].provider == "OpenAI" for m in openai_models))
        self.assertIn("gpt-4.5", openai_models)
        self.assertIn("o3", openai_models)

    def test_dynamic_custom_model_lifecycle(self):
        model_name = "test-custom-finetune-xyz"
        pricing = ModelPricing(
            provider="CustomOrg",
            name=model_name,
            input_per_m=0.88,
            output_per_m=2.44,
        )
        save_custom_model(pricing)
        retrieved = get_model_pricing(model_name)
        self.assertEqual(retrieved.provider, "CustomOrg")
        self.assertEqual(retrieved.input_per_m, 0.88)

        # Cleanup
        removed = remove_custom_model(model_name)
        self.assertTrue(removed)


if __name__ == "__main__":
    unittest.main()
