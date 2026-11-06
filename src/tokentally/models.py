"""
Model registry and pricing definitions for major LLM providers.
Prices are represented in USD per 1,000,000 tokens.
Supports dynamic local pricing overrides via ~/.tokentally/pricing.json
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModelPricing:
    """Pricing specifications for a specific model."""
    provider: str
    name: str
    input_per_m: float
    output_per_m: float
    cached_input_per_m: Optional[float] = None
    context_window: int = 128000
    description: str = ""
    is_local: bool = False

    @property
    def has_caching(self) -> bool:
        return self.cached_input_per_m is not None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Built-in canonical registry of leading frontier, open-source, and cloud models (USD per 1M tokens)
_BUILTIN_REGISTRY: Dict[str, ModelPricing] = {
    # OpenAI Frontier & Reasoning
    "gpt-4.5": ModelPricing(
        provider="OpenAI",
        name="gpt-4.5",
        input_per_m=75.00,
        output_per_m=150.00,
        cached_input_per_m=37.50,
        context_window=128000,
        description="OpenAI Orion frontier model with world knowledge and deep contextual synthesis",
    ),
    "o3": ModelPricing(
        provider="OpenAI",
        name="o3",
        input_per_m=10.00,
        output_per_m=40.00,
        cached_input_per_m=5.00,
        context_window=200000,
        description="Flagship OpenAI o3 deep reasoning model for competitive programming and research",
    ),
    "o3-pro": ModelPricing(
        provider="OpenAI",
        name="o3-pro",
        input_per_m=20.00,
        output_per_m=80.00,
        cached_input_per_m=10.00,
        context_window=200000,
        description="High-compute o3 model for extended verification and mission-critical logic",
    ),
    "o3-mini": ModelPricing(
        provider="OpenAI",
        name="o3-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=200000,
        description="High-speed reasoning model balancing coding depth and low latency",
    ),
    "o1": ModelPricing(
        provider="OpenAI",
        name="o1",
        input_per_m=15.00,
        output_per_m=60.00,
        cached_input_per_m=7.50,
        context_window=200000,
        description="State of the art deep reasoning model with internal chain of thought",
    ),
    "o1-mini": ModelPricing(
        provider="OpenAI",
        name="o1-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=128000,
        description="Fast reasoning model optimized for coding, mathematics, and STEM",
    ),
    "gpt-4o": ModelPricing(
        provider="OpenAI",
        name="gpt-4o",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="Flagship multimodal omni model for general intelligence and multimodal coding",
    ),
    "gpt-4o-mini": ModelPricing(
        provider="OpenAI",
        name="gpt-4o-mini",
        input_per_m=0.15,
        output_per_m=0.60,
        cached_input_per_m=0.075,
        context_window=128000,
        description="Fast, cost-efficient small model for high-frequency tasks",
    ),
    "gpt-4-turbo": ModelPricing(
        provider="OpenAI",
        name="gpt-4-turbo",
        input_per_m=10.00,
        output_per_m=30.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Previous generation GPT-4 Turbo model",
    ),
    "gpt-3.5-turbo": ModelPricing(
        provider="OpenAI",
        name="gpt-3.5-turbo",
        input_per_m=0.50,
        output_per_m=1.50,
        cached_input_per_m=None,
        context_window=16385,
        description="Legacy lightweight model",
    ),

    # Anthropic Claude 3.5 & 3.7
    "claude-3-7-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-3-7-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Hybrid standard and extended-thinking frontier coding model",
    ),
    "claude-3-5-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="High-intelligence industry standard for autonomous agents and codebases",
    ),
    "claude-3-5-haiku": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-haiku",
        input_per_m=0.80,
        output_per_m=4.00,
        cached_input_per_m=0.08,
        context_window=200000,
        description="Ultra-fast, responsive lightweight model for edge processing",
    ),
    "claude-3-5-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="Anthropic frontier high-compute model for deep complex architectures",
    ),
    "claude-3-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="Deep contextual synthesis and long-form analysis",
    ),

    # Google Gemini 2.0 & 2.5
    "gemini-2.5-pro": ModelPricing(
        provider="Google",
        name="gemini-2.5-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=1000000,
        description="Advanced reasoning multimodal model with 1M context window",
    ),
    "gemini-2.5-flash": ModelPricing(
        provider="Google",
        name="gemini-2.5-flash",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Cost-optimized high-speed multimodal model",
    ),
    "gemini-2.0-flash-thinking": ModelPricing(
        provider="Google",
        name="gemini-2.0-flash-thinking",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Gemini Flash with integrated reasoning and verifiable thinking traces",
    ),
    "gemini-2.0-flash": ModelPricing(
        provider="Google",
        name="gemini-2.0-flash",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Real-time multimodal streaming model",
    ),
    "gemini-2.0-pro": ModelPricing(
        provider="Google",
        name="gemini-2.0-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=2000000,
        description="Frontier multimodal Gemini 2.0 Pro model with 2M context window",
    ),
    "gemini-1.5-pro": ModelPricing(
        provider="Google",
        name="gemini-1.5-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=2000000,
        description="Ultra-long 2M context window model",
    ),
    "gemini-1.5-flash": ModelPricing(
        provider="Google",
        name="gemini-1.5-flash",
        input_per_m=0.075,
        output_per_m=0.30,
        cached_input_per_m=0.01875,
        context_window=1000000,
        description="Ultra-low cost high-volume model",
    ),

    # xAI Grok
    "grok-3": ModelPricing(
        provider="xAI",
        name="grok-3",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.75,
        context_window=131072,
        description="xAI flagship frontier intelligence and coding model",
    ),
    "grok-3-mini": ModelPricing(
        provider="xAI",
        name="grok-3-mini",
        input_per_m=0.30,
        output_per_m=1.50,
        cached_input_per_m=0.075,
        context_window=131072,
        description="High-speed lightweight reasoning model by xAI",
    ),
    "grok-2": ModelPricing(
        provider="xAI",
        name="grok-2",
        input_per_m=2.00,
        output_per_m=10.00,
        cached_input_per_m=0.50,
        context_window=131072,
        description="xAI multimodal general capability model",
    ),
    "grok-2-mini": ModelPricing(
        provider="xAI",
        name="grok-2-mini",
        input_per_m=0.20,
        output_per_m=1.00,
        cached_input_per_m=0.05,
        context_window=131072,
        description="Compact xAI inference model for low-latency queries",
    ),
        # DeepSeek
    "deepseek-v3": ModelPricing(
        provider="DeepSeek",
        name="deepseek-v3",
        input_per_m=0.14,
        output_per_m=0.28,
        cached_input_per_m=0.014,
        context_window=64000,
        description="Leading open-architecture frontier MoE model",
    ),
    "deepseek-r1": ModelPricing(
        provider="DeepSeek",
        name="deepseek-r1",
        input_per_m=0.55,
        output_per_m=2.19,
        cached_input_per_m=0.14,
        context_window=64000,
        description="Reinforcement learning reasoning model with verifiable CoT",
    ),

    # Mistral AI
    "mistral-saba": ModelPricing(
        provider="Mistral",
        name="mistral-saba",
        input_per_m=0.20,
        output_per_m=0.60,
        cached_input_per_m=None,
        context_window=32768,
        description="High-throughput reasoning model fine-tuned for Middle Eastern and Indic domains",
    ),
    "pixtral-large": ModelPricing(
        provider="Mistral",
        name="pixtral-large",
        input_per_m=2.00,
        output_per_m=6.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Mistral 124B parameter multimodal multimodal reasoning frontier model",
    ),
    "pixtral-12b": ModelPricing(
        provider="Mistral",
        name="pixtral-12b",
        input_per_m=0.15,
        output_per_m=0.15,
        cached_input_per_m=None,
        context_window=128000,
        description="Lightweight multimodal visual inspection model",
    ),
    "codestral-2501": ModelPricing(
        provider="Mistral",
        name="codestral-2501",
        input_per_m=0.30,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=256000,
        description="Latest generation code synthesis and fill-in-the-middle model",
    ),
    "mistral-large": ModelPricing(
        provider="Mistral",
        name="mistral-large",
        input_per_m=2.00,
        output_per_m=6.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Mistral flagship frontier model for reasoning and coding",
    ),
    "codestral": ModelPricing(
        provider="Mistral",
        name="codestral",
        input_per_m=0.30,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=256000,
        description="Specialized code generation and fill-in-the-middle model",
    ),
    "mistral-small": ModelPricing(
        provider="Mistral",
        name="mistral-small",
        input_per_m=0.10,
        output_per_m=0.30,
        cached_input_per_m=None,
        context_window=128000,
        description="Fast low-latency edge model",
    ),

    # Groq / Cerebras Hosted LPUs (Per million tokens)
    "groq-llama-3.3-70b": ModelPricing(
        provider="Groq",
        name="groq-llama-3.3-70b",
        input_per_m=0.59,
        output_per_m=0.79,
        cached_input_per_m=None,
        context_window=128000,
        description="Ultra-high throughput LPU hosted 70B parameter model",
    ),
    "groq-mixtral-8x7b": ModelPricing(
        provider="Groq",
        name="groq-mixtral-8x7b",
        input_per_m=0.24,
        output_per_m=0.24,
        cached_input_per_m=None,
        context_window=32768,
        description="Fast MoE inference on Groq LPUs",
    ),

    # Cerebras Wafer-Scale Engine
    "cerebras-llama-3.3-70b": ModelPricing(
        provider="Cerebras",
        name="cerebras-llama-3.3-70b",
        input_per_m=0.60,
        output_per_m=0.60,
        cached_input_per_m=None,
        context_window=128000,
        description="Sub-second 70B inference on Cerebras CS-3",
    ),
    "cerebras-llama-3.1-8b": ModelPricing(
        provider="Cerebras",
        name="cerebras-llama-3.1-8b",
        input_per_m=0.10,
        output_per_m=0.10,
        cached_input_per_m=None,
        context_window=128000,
        description="Ultra-low latency 8B inference on Cerebras CS-3",
    ),

    # Cohere
    "command-r": ModelPricing(
        provider="Cohere",
        name="command-r",
        input_per_m=0.15,
        output_per_m=0.60,
        cached_input_per_m=0.075,
        context_window=128000,
        description="Cohere scalable RAG and enterprise tool use model",
    ),
    "command-r-plus": ModelPricing(
        provider="Cohere",
        name="command-r-plus",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="Cohere flagship enterprise multi-step reasoning model",
    ),

    # AWS Bedrock
    "bedrock-claude-3-7-sonnet": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-claude-3-7-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Claude 3.7 Sonnet deployed on AWS Bedrock",
    ),
    "bedrock-claude-3-5-sonnet": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-claude-3-5-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Anthropic Claude 3.5 Sonnet hosted via Amazon Bedrock",
    ),
    "bedrock-nova-pro": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-pro",
        input_per_m=0.80,
        output_per_m=3.20,
        cached_input_per_m=0.20,
        context_window=300000,
        description="Amazon Nova Pro multimodal reasoning model",
    ),
    "bedrock-nova-lite": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-lite",
        input_per_m=0.06,
        output_per_m=0.24,
        cached_input_per_m=0.015,
        context_window=300000,
        description="Amazon Nova Lite ultra-low cost high-speed model",
    ),
    "bedrock-nova-micro": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-micro",
        input_per_m=0.035,
        output_per_m=0.14,
        cached_input_per_m=None,
        context_window=128000,
        description="Amazon Nova Micro text-only low latency model",
    ),

    # Alibaba Qwen
    "qwen-2.5-max": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-2.5-max",
        input_per_m=1.60,
        output_per_m=6.40,
        cached_input_per_m=None,
        context_window=128000,
        description="Qwen flagship frontier dense model matching frontier benchmarks",
    ),
    "qwen-2.5-coder-32b": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-2.5-coder-32b",
        input_per_m=0.20,
        output_per_m=0.20,
        cached_input_per_m=None,
        context_window=128000,
        description="Specialized high-capability open coding model",
    ),
    "qwen-2.5-72b": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-2.5-72b",
        input_per_m=0.35,
        output_per_m=0.40,
        cached_input_per_m=None,
        context_window=128000,
        description="General open-weights flagship multilingual model",
    ),

    # Meta LLaMA 3.3, 3.2, 3.1
    "llama-3.3-70b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.3-70b",
        input_per_m=0.70,
        output_per_m=0.80,
        cached_input_per_m=None,
        context_window=128000,
        description="Flagship open weights 70B model",
    ),
    "llama-3.2-90b-vision": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-90b-vision",
        input_per_m=0.90,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=128000,
        description="Meta vision multimodal flagship 90B model",
    ),
    "llama-3.2-11b-vision": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-11b-vision",
        input_per_m=0.16,
        output_per_m=0.16,
        cached_input_per_m=None,
        context_window=128000,
        description="Meta lightweight vision multimodal 11B model",
    ),
    "llama-3.2-3b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-3b",
        input_per_m=0.04,
        output_per_m=0.04,
        cached_input_per_m=None,
        context_window=128000,
        description="Edge and on-device compact 3B model",
    ),
    "llama-3.2-1b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-1b",
        input_per_m=0.02,
        output_per_m=0.02,
        cached_input_per_m=None,
        context_window=128000,
        description="Micro-instance 1B model for high-throughput classification",
    ),
    "llama-3.1-405b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.1-405b",
        input_per_m=2.50,
        output_per_m=2.50,
        cached_input_per_m=None,
        context_window=128000,
        description="Frontier scale open weights 405B model",
    ),
    "llama-3.1-8b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.1-8b",
        input_per_m=0.05,
        output_per_m=0.05,
        cached_input_per_m=None,
        context_window=128000,
        description="Lightweight 8B open model for local or micro-instance deployment",
    ),

    # Ollama / Local Models (Zero dollar inference cost)
    "ollama-local": ModelPricing(
        provider="Ollama (Local)",
        name="ollama-local",
        input_per_m=0.00,
        output_per_m=0.00,
        cached_input_per_m=0.00,
        context_window=128000,
        description="Local on-device inference via Ollama / llama.cpp",
        is_local=True,
    ),
    "vllm-local": ModelPricing(
        provider="vLLM (Self-Hosted)",
        name="vllm-local",
        input_per_m=0.00,
        output_per_m=0.00,
        cached_input_per_m=0.00,
        context_window=128000,
        description="Self-hosted PagedAttention inference server with zero per-token API charges",
        is_local=True,
    ),
}

# User aliases for fast shorthand CLI typing
MODEL_ALIASES = {
    "4.5": "gpt-4.5",
    "4o": "gpt-4o",
    "4o-mini": "gpt-4o-mini",
    "o1-preview": "o1",
    "o3": "o3",
    "o3m": "o3-mini",
    "o3-mini": "o3-mini",
    "o3-full": "o3",
    "sonnet": "claude-3-7-sonnet",
    "sonnet-3.7": "claude-3-7-sonnet",
    "sonnet-3.5": "claude-3-5-sonnet",
    "haiku": "claude-3-5-haiku",
    "opus": "claude-3-5-opus",
    "flash": "gemini-2.5-flash",
    "gemini-flash": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-pro",
    "thinking": "gemini-2.0-flash-thinking",
    "grok": "grok-3",
    "grok-mini": "grok-3-mini",
    "deepseek": "deepseek-v3",
    "r1": "deepseek-r1",
    "mistral": "mistral-large",
    "saba": "mistral-saba",
    "cohere": "command-r",
    "command": "command-r",
    "qwen": "qwen-2.5-coder-32b",
    "qwen-max": "qwen-2.5-max",
    "cerebras": "cerebras-llama-3.3-70b",
    "groq": "groq-llama-3.3-70b",
    "nova": "bedrock-nova-pro",
    "bedrock": "bedrock-claude-3-7-sonnet",
    "local": "ollama-local",
    "ollama": "ollama-local",
    "vllm": "vllm-local",
}


def sync_live_models(source_url: Optional[str] = None, timeout: float = 10.0) -> int:
    """
    Synchronize live pricing and context windows for thousands of frontier and open-source models
    from the global open pricing registry.
    Saves to ~/.tokentally/community_pricing.json.
    Returns the count of successfully synchronized models.
    """
    url = source_url or "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    import urllib.request
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "tokentally-cli"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read().decode("utf-8")
        data = json.loads(content)

    parsed: Dict[str, Any] = {}
    for k, v in data.items():
        if not isinstance(v, dict) or k == "sample_spec":
            continue
        in_cost = v.get("input_cost_per_token")
        out_cost = v.get("output_cost_per_token")
        if in_cost is None or out_cost is None:
            continue
        in_m = round(float(in_cost) * 1_000_000, 4)
        out_m = round(float(out_cost) * 1_000_000, 4)
        cached_m = round(float(v["cache_read_input_token_cost"]) * 1_000_000, 4) if v.get("cache_read_input_token_cost") is not None else None
        ctx = int(v.get("max_input_tokens") or v.get("max_tokens") or 128000)
        provider = v.get("litellm_provider") or "Community"

        parsed[k.lower()] = {
            "provider": provider.capitalize() if isinstance(provider, str) else "Community",
            "name": k.lower(),
            "input_per_m": in_m,
            "output_per_m": out_m,
            "cached_input_per_m": cached_m,
            "context_window": ctx,
            "description": f"Live synced model ({provider})",
        }

    cfg_dir = Path.home() / ".tokentally"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cfg_dir / "community_pricing.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)

    # Refresh in-memory registry
    global MODEL_REGISTRY
    MODEL_REGISTRY = get_full_registry()
    return len(parsed)


def _load_user_custom_pricing() -> Dict[str, ModelPricing]:
    """Load community synchronized models, local user pricing, and tokentally.toml overrides."""
    custom: Dict[str, ModelPricing] = {}
    cfg_dir = Path.home() / ".tokentally"

    # 1. Load community cached pricing if available
    comm_file = cfg_dir / "community_pricing.json"
    if comm_file.is_file():
        try:
            with open(comm_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    cached_val = val.get("cached_input_per_m")
                    custom[key] = ModelPricing(
                        provider=val.get("provider", "Community"),
                        name=key,
                        input_per_m=float(val.get("input_per_m", 0.0)),
                        output_per_m=float(val.get("output_per_m", 0.0)),
                        cached_input_per_m=float(cached_val) if cached_val is not None else None,
                        context_window=int(val.get("context_window", 128000)),
                        description=val.get("description", "Community registry"),
                    )
        except Exception:
            pass

    # 2. Load manual overrides from ~/.tokentally/pricing.json
    cfg_file = cfg_dir / "pricing.json"
    if cfg_file.is_file():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    cached_val = val.get("cached_input_per_m")
                    custom[key] = ModelPricing(
                        provider=val.get("provider", "Custom"),
                        name=key,
                        input_per_m=float(val.get("input_per_m", 0.0)),
                        output_per_m=float(val.get("output_per_m", 0.0)),
                        cached_input_per_m=float(cached_val) if cached_val is not None else None,
                        context_window=int(val.get("context_window", 128000)),
                        description=val.get("description", "Custom user pricing definition"),
                    )
        except Exception:
            pass

    # 3. Load from local repository tokentally.toml if present
    try:
        from .config import load_config
        cfg = load_config()
        if cfg.custom_models:
            for key, val in cfg.custom_models.items():
                cached_val = val.get("cached_input_per_m")
                custom[key] = ModelPricing(
                    provider=val.get("provider", "Local Config"),
                    name=key,
                    input_per_m=float(val.get("input_per_m", 0.0)),
                    output_per_m=float(val.get("output_per_m", 0.0)),
                    cached_input_per_m=float(cached_val) if cached_val is not None else None,
                    context_window=int(val.get("context_window", 128000)),
                    description=val.get("description", "Declared in tokentally.toml"),
                )
    except Exception:
        pass

    return custom


def save_custom_model(pricing: ModelPricing) -> None:
    """Save or update a custom model pricing in ~/.tokentally/pricing.json."""
    cfg_dir = Path.home() / ".tokentally"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "pricing.json"
    data: Dict[str, Any] = {}
    if cfg_file.is_file():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    data[pricing.name] = {
        "provider": pricing.provider,
        "input_per_m": pricing.input_per_m,
        "output_per_m": pricing.output_per_m,
        "cached_input_per_m": pricing.cached_input_per_m,
        "context_window": pricing.context_window,
        "description": pricing.description,
    }

    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Refresh global registry
    global MODEL_REGISTRY
    MODEL_REGISTRY = get_full_registry()


def remove_custom_model(name: str) -> bool:
    """Remove a custom model definition from ~/.tokentally/pricing.json."""
    cfg_dir = Path.home() / ".tokentally"
    cfg_file = cfg_dir / "pricing.json"
    if not cfg_file.is_file():
        return False

    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if name in data:
            del data[name]
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            global MODEL_REGISTRY
            MODEL_REGISTRY = get_full_registry()
            return True
    except Exception:
        pass
    return False


def get_full_registry() -> Dict[str, ModelPricing]:
    """Combine built-in registry with user-defined overrides and live sync cache."""
    reg = dict(_BUILTIN_REGISTRY)
    reg.update(_load_user_custom_pricing())
    return reg


MODEL_REGISTRY = get_full_registry()


def normalize_model_name(name: str) -> str:
    """
    Intelligently normalize user-entered model names, resolving aliases,
    stripping repository/organization prefixes (e.g. 'openai/gpt-4.5' -> 'gpt-4.5'),
    and stripping revision dates or release tags (e.g. 'claude-3-7-sonnet-20250219' -> 'claude-3-7-sonnet').
    """
    if not name:
        return "gpt-4o"
    cleaned = name.strip().lower()

    # Exact canonical match takes precedence over aliases
    reg = get_full_registry()
    if cleaned in reg:
        return cleaned

    # Direct alias match
    if cleaned in MODEL_ALIASES:
        return MODEL_ALIASES[cleaned]

    # Strip provider prefix: "openai/gpt-4o" -> "gpt-4o"
    if "/" in cleaned:
        unprefixed = cleaned.split("/")[-1]
        if unprefixed in MODEL_ALIASES:
            return MODEL_ALIASES[unprefixed]
        if unprefixed in reg:
            return unprefixed
        cleaned = unprefixed

    # Strip version date patterns, e.g. -20241022, -2025-02-19, -001, -latest
    stripped = re.sub(r"-\d{4}-?\d{2}-?\d{2}$", "", cleaned)
    stripped = re.sub(r"-(latest|preview|exp|001|002|instruct)$", "", stripped)

    if stripped in MODEL_ALIASES:
        return MODEL_ALIASES[stripped]
    if stripped in reg:
        return stripped

    # Substring prefix matching for canonical families
    for key in reg:
        if cleaned.startswith(key):
            return key

    return cleaned


def get_model_pricing(name: str) -> ModelPricing:
    """Retrieve pricing specs for a given model or alias. Raises KeyError if unknown."""
    norm = normalize_model_name(name)
    reg = get_full_registry()
    if norm in reg:
        return reg[norm]
    raise KeyError(
        f"Unknown model: '{name}'. Run 'tokentally models --sync' to update the registry, or use 'tokentally models --search <name>' to find matching IDs."
    )


def list_supported_models(
    search: Optional[str] = None,
    provider: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[str]:
    """Return sorted list of supported canonical model identifiers matching search or provider filters."""
    reg = get_full_registry()
    keys = list(reg.keys())

    if search:
        s = search.strip().lower()
        keys = [k for k in keys if s in k.lower() or s in reg[k].description.lower()]

    if provider:
        p = provider.strip().lower()
        keys = [k for k in keys if p in reg[k].provider.lower()]

    keys.sort()
    if limit is not None and limit > 0:
        return keys[:limit]
    return keys
