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

    def test_frontier_2026_gemini_gpt_claude(self):
        # Google Gemini 3.8 & Gemini 4 Argon
        p_g38 = get_model_pricing("gemini-3.8")
        self.assertEqual(p_g38.input_per_m, 1.25)
        self.assertEqual(p_g38.context_window, 2000000)

        p_g38_live = get_model_pricing("gemini-3.8-live")
        self.assertEqual(p_g38_live.input_per_m, 0.15)
        self.assertEqual(p_g38_live.output_per_m, 0.60)

        p_g4_argon = get_model_pricing("gemini-4-argon")
        self.assertEqual(p_g4_argon.input_per_m, 1.50)
        self.assertEqual(p_g4_argon.output_per_m, 6.00)

        p_g4_think = get_model_pricing("gemini-4-argon-thinking")
        self.assertEqual(p_g4_think.input_per_m, 0.35)

        # Anthropic Claude 3.8 & 4
        p_c4_sonnet = get_model_pricing("claude-4-sonnet")
        self.assertEqual(p_c4_sonnet.input_per_m, 3.00)
        self.assertEqual(p_c4_sonnet.context_window, 300000)

        p_c4_opus = get_model_pricing("claude-4-opus")
        self.assertEqual(p_c4_opus.input_per_m, 15.00)

        p_c38_sonnet = get_model_pricing("claude-3-8-sonnet")
        self.assertEqual(p_c38_sonnet.input_per_m, 3.00)

        # OpenAI 2026 releases: GPT-5, Luma, Sol, Astra, o4
        p_gpt5 = get_model_pricing("gpt-5")
        self.assertEqual(p_gpt5.input_per_m, 15.00)
        self.assertEqual(p_gpt5.context_window, 256000)

        p_luma = get_model_pricing("gpt-luma")
        self.assertEqual(p_luma.input_per_m, 2.50)
        self.assertEqual(p_luma.output_per_m, 10.00)

        p_sol = get_model_pricing("gpt-sol")
        self.assertEqual(p_sol.input_per_m, 0.20)
        self.assertEqual(p_sol.output_per_m, 0.80)

        p_astra = get_model_pricing("gpt-astra")
        self.assertEqual(p_astra.input_per_m, 10.00)
        self.assertEqual(p_astra.output_per_m, 40.00)

        p_o4 = get_model_pricing("o4")
        self.assertEqual(p_o4.input_per_m, 10.00)
        self.assertEqual(p_o4.output_per_m, 40.00)

    def test_global_organizations_frontier_2026(self):
        # Meta LLaMA 4
        p_mav = get_model_pricing("llama-4-maverick")
        self.assertEqual(p_mav.input_per_m, 0.70)
        self.assertEqual(p_mav.context_window, 256000)
        p_beh = get_model_pricing("llama-4-behemoth")
        self.assertEqual(p_beh.input_per_m, 2.00)
        p_scout = get_model_pricing("llama-4-scout")
        self.assertEqual(p_scout.input_per_m, 0.15)

        # DeepSeek V4 & R2
        p_v4 = get_model_pricing("deepseek-v4")
        self.assertEqual(p_v4.input_per_m, 0.18)
        self.assertEqual(p_v4.output_per_m, 0.36)
        p_r2 = get_model_pricing("deepseek-r2")
        self.assertEqual(p_r2.input_per_m, 0.65)
        self.assertEqual(p_r2.cached_input_per_m, 0.16)

        # xAI Grok 3.5 & DeepSearch
        p_grok35 = get_model_pricing("grok-3.5")
        self.assertEqual(p_grok35.input_per_m, 3.00)
        p_deepsearch = get_model_pricing("grok-3-deepsearch")
        self.assertEqual(p_deepsearch.input_per_m, 5.00)
        self.assertEqual(p_deepsearch.output_per_m, 25.00)

        # Mistral Devstral & Large 3
        p_devstral = get_model_pricing("devstral")
        self.assertEqual(p_devstral.input_per_m, 0.30)
        p_mlarge3 = get_model_pricing("mistral-large-3")
        self.assertEqual(p_mlarge3.input_per_m, 2.00)

        # Microsoft Phi-4
        p_phi4 = get_model_pricing("phi-4")
        self.assertEqual(p_phi4.provider, "Microsoft")
        self.assertEqual(p_phi4.input_per_m, 0.07)
        self.assertEqual(p_phi4.output_per_m, 0.14)

        # Apple Private Cloud Compute & On-Device
        p_pcc = get_model_pricing("apple-pcc-server")
        self.assertEqual(p_pcc.provider, "Apple")
        self.assertEqual(p_pcc.input_per_m, 0.25)
        p_aon = get_model_pricing("apple-intelligence-local")
        self.assertEqual(p_aon.input_per_m, 0.00)
        self.assertTrue(p_aon.is_local)

        # Cohere Command A & Command R7B
        p_cmda = get_model_pricing("command-a")
        self.assertEqual(p_cmda.input_per_m, 1.50)
        p_cmdr7b = get_model_pricing("command-r7b")
        self.assertEqual(p_cmdr7b.input_per_m, 0.0375)

        # Alibaba Qwen 3
        p_qw3 = get_model_pricing("qwen-3-max")
        self.assertEqual(p_qw3.input_per_m, 1.60)
        p_qw3_coder = get_model_pricing("qwen-3-coder-32b")
        self.assertEqual(p_qw3_coder.input_per_m, 0.20)

        # AWS Bedrock Nova Premier
        p_nova_prem = get_model_pricing("bedrock-nova-premier")
        self.assertEqual(p_nova_prem.input_per_m, 2.00)

        # Baidu Ernie
        p_ernie = get_model_pricing("ernie-4.0-turbo")
        self.assertEqual(p_ernie.provider, "Baidu")
        self.assertEqual(p_ernie.input_per_m, 0.40)

        # TII Falcon 3
        p_falcon = get_model_pricing("falcon-3-40b")
        self.assertEqual(p_falcon.input_per_m, 0.30)

        # Hosted LPUs: Groq & Cerebras DeepSeek R1
        p_groq_r1 = get_model_pricing("groq-deepseek-r1")
        self.assertEqual(p_groq_r1.input_per_m, 0.75)
        p_cs_r1 = get_model_pricing("cerebras-deepseek-r1")
        self.assertEqual(p_cs_r1.input_per_m, 0.70)

    def test_adaptive_heuristic_tier_inference(self):
        # Uncataloged future models dynamically infer tier without raising KeyError
        inferred_g5 = get_model_pricing("gemini-5-pro")
        self.assertTrue(inferred_g5.is_inferred)
        self.assertEqual(inferred_g5.input_per_m, 1.25)
        self.assertEqual(inferred_g5.provider, "Google (Inferred)")

        inferred_c5 = get_model_pricing("claude-5-opus")
        self.assertTrue(inferred_c5.is_inferred)
        self.assertEqual(inferred_c5.input_per_m, 15.00)

        inferred_sol_micro = get_model_pricing("gpt-future-sol-micro")
        self.assertTrue(inferred_sol_micro.is_inferred)
        self.assertEqual(inferred_sol_micro.input_per_m, 0.15)

        # Cost estimation passes through inference flag
        calc = CostCalculator()
        res = calc.estimate("Sample prompt", model="gemini-5-pro", completion_tokens=100)
        self.assertTrue(res.is_inferred)
        self.assertIn("Inferred based on Google", res.inference_notes)

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
