"""
Model registry and pricing definitions for major LLM providers.
Prices are represented in USD per 1,000,000 tokens.
Supports dynamic local pricing overrides via ~/.tokentally/pricing.json
"""

import json
import os
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
    # OpenAI
    "gpt-4o": ModelPricing(
        provider="OpenAI",
        name="gpt-4o",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="Flagship multimodal omni model for complex reasoning and multimodal coding",
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
    "o3-mini": ModelPricing(
        provider="OpenAI",
        name="o3-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=200000,
        description="Next-generation reasoning model balancing extreme speed and deep logic",
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

    # Anthropic
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
    "claude-3-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="Deep contextual synthesis and long-form analysis",
    ),

    # Google
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
    "gemini-2.0-flash": ModelPricing(
        provider="Google",
        name="gemini-2.0-flash",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Real-time multi-modal streaming model",
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

    # Meta LLaMA Standard Hosted
    "llama-3.3-70b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.3-70b",
        input_per_m=0.70,
        output_per_m=0.80,
        cached_input_per_m=None,
        context_window=128000,
        description="Flagship open weights 70B model",
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
        description="Local on-device inference via Ollama / vLLM / llama.cpp",
        is_local=True,
    ),
}

# User aliases for fast shorthand CLI typing
MODEL_ALIASES = {
    "4o": "gpt-4o",
    "4o-mini": "gpt-4o-mini",
    "o1-preview": "o1",
    "o3": "o3-mini",
    "sonnet": "claude-3-5-sonnet",
    "sonnet-3.7": "claude-3-7-sonnet",
    "sonnet-3.5": "claude-3-5-sonnet",
    "haiku": "claude-3-5-haiku",
    "flash": "gemini-2.5-flash",
    "gemini-flash": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-pro",
    "deepseek": "deepseek-v3",
    "r1": "deepseek-r1",
    "mistral": "mistral-large",
    "local": "ollama-local",
    "ollama": "ollama-local",
}


def _load_user_custom_pricing() -> Dict[str, ModelPricing]:
    """Load local user-defined pricing overrides from ~/.tokentally/pricing.json."""
    custom: Dict[str, ModelPricing] = {}
    cfg_dir = Path.home() / ".tokentally"
    cfg_file = cfg_dir / "pricing.json"
    if cfg_file.is_file():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    custom[key] = ModelPricing(
                        provider=val.get("provider", "Custom"),
                        name=key,
                        input_per_m=float(val.get("input_per_m", 0.0)),
                        output_per_m=float(val.get("output_per_m", 0.0)),
                        cached_input_per_m=float(val["cached_input_per_m"]) if "cached_input_per_m" in val else None,
                        context_window=int(val.get("context_window", 128000)),
                        description=val.get("description", "Custom user pricing definition"),
                    )
        except Exception:
            pass
    return custom


def get_full_registry() -> Dict[str, ModelPricing]:
    """Combine built-in registry with user-defined overrides."""
    reg = dict(_BUILTIN_REGISTRY)
    reg.update(_load_user_custom_pricing())
    return reg


MODEL_REGISTRY = get_full_registry()


def normalize_model_name(name: str) -> str:
    """Normalize user-entered model names, resolving aliases and case."""
    cleaned = name.strip().lower()
    return MODEL_ALIASES.get(cleaned, cleaned)


def get_model_pricing(name: str) -> ModelPricing:
    """Retrieve pricing specs for a given model or alias. Raises KeyError if unknown."""
    norm = normalize_model_name(name)
    reg = get_full_registry()
    if norm in reg:
        return reg[norm]
    raise KeyError(
        f"Unknown model: '{name}'. Supported models: {', '.join(reg.keys())}"
    )


def list_supported_models() -> List[str]:
    """Return sorted list of all supported canonical model identifiers."""
    reg = get_full_registry()
    return sorted(list(reg.keys()))
