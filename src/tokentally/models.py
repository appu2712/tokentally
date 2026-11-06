"""
Model registry and pricing definitions for major LLM providers.
Prices are represented in USD per 1,000,000 tokens.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


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

    @property
    def has_caching(self) -> bool:
        return self.cached_input_per_m is not None


# Complete registry of leading models with verified standard public API pricing (USD per 1M tokens)
MODEL_REGISTRY: Dict[str, ModelPricing] = {
    # OpenAI
    "gpt-4o": ModelPricing(
        provider="OpenAI",
        name="gpt-4o",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="Flagship multimodal omni model for high-intelligence reasoning",
    ),
    "gpt-4o-mini": ModelPricing(
        provider="OpenAI",
        name="gpt-4o-mini",
        input_per_m=0.15,
        output_per_m=0.60,
        cached_input_per_m=0.075,
        context_window=128000,
        description="Fast, cost-efficient small model for everyday high-volume tasks",
    ),
    "o1": ModelPricing(
        provider="OpenAI",
        name="o1",
        input_per_m=15.00,
        output_per_m=60.00,
        cached_input_per_m=7.50,
        context_window=200000,
        description="Deep reasoning model with internal chain of thought",
    ),
    "o1-mini": ModelPricing(
        provider="OpenAI",
        name="o1-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=128000,
        description="Fast reasoning model optimized for coding and STEM",
    ),
    "o3-mini": ModelPricing(
        provider="OpenAI",
        name="o3-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=200000,
        description="Next-generation reasoning model balancing speed and deep logic",
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
        description="Hybrid standard and extended-thinking frontier model",
    ),
    "claude-3-5-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="High-intelligence industry standard for coding and agents",
    ),
    "claude-3-5-haiku": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-haiku",
        input_per_m=0.80,
        output_per_m=4.00,
        cached_input_per_m=0.08,
        context_window=200000,
        description="Ultra-fast, responsive lightweight model",
    ),
    "claude-3-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="High-tier complex analysis model",
    ),

    # Google
    "gemini-2.5-pro": ModelPricing(
        provider="Google",
        name="gemini-2.5-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=1000000,
        description="Advanced reasoning multimodal model with 1M context",
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
        description="Long context frontier model",
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
        description="State of the art open-weight architecture model",
    ),
    "deepseek-r1": ModelPricing(
        provider="DeepSeek",
        name="deepseek-r1",
        input_per_m=0.55,
        output_per_m=2.19,
        cached_input_per_m=0.14,
        context_window=64000,
        description="Reinforcement-learning driven open reasoning model",
    ),

    # Meta LLaMA (Hosted standard API references)
    "llama-3.3-70b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.3-70b",
        input_per_m=0.70,
        output_per_m=0.80,
        cached_input_per_m=None,
        context_window=128000,
        description="Flagship open weights 70B parameter model",
    ),
    "llama-3.1-8b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.1-8b",
        input_per_m=0.05,
        output_per_m=0.05,
        cached_input_per_m=None,
        context_window=128000,
        description="Lightweight open weights edge model",
    ),
}

# Common user aliases
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
}


def normalize_model_name(name: str) -> str:
    """Normalize user-entered model names, handling aliases and case."""
    cleaned = name.strip().lower()
    return MODEL_ALIASES.get(cleaned, cleaned)


def get_model_pricing(name: str) -> ModelPricing:
    """Retrieve pricing specs for a given model or alias. Raises KeyError if unknown."""
    norm = normalize_model_name(name)
    if norm in MODEL_REGISTRY:
        return MODEL_REGISTRY[norm]
    raise KeyError(
        f"Unknown model: '{name}'. Supported models: {', '.join(MODEL_REGISTRY.keys())}"
    )


def list_supported_models() -> List[str]:
    """Return sorted list of all supported canonical model identifiers."""
    return sorted(list(MODEL_REGISTRY.keys()))
