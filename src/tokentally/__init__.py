"""
tokentally - Fast Token Counter, LLM Cost Estimator & Context Packer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A unified developer library and CLI to count tokens, estimate exact multi-model costs,
pack repositories for LLM prompts, and enforce CI/CD budget guardrails across
OpenAI, Claude, Gemini, DeepSeek, and open-source models.
"""

from .models import (
    MODEL_REGISTRY,
    ModelPricing,
    get_model_pricing,
    list_supported_models,
)
from .counter import (
    TokenCounter,
    count_tokens,
    get_model_encoding,
)
from .calculator import (
    CostCalculator,
    CostResult,
    ModelComparisonRow,
    estimate_cost,
    compare_models,
)
from .packer import (
    RepositoryPacker,
    PackResult,
    pack_repository,
)
from .guard import (
    BudgetGuard,
    GuardResult,
    check_budget,
)

__version__ = "0.1.0"
__all__ = [
    "MODEL_REGISTRY",
    "ModelPricing",
    "get_model_pricing",
    "list_supported_models",
    "TokenCounter",
    "count_tokens",
    "get_model_encoding",
    "CostCalculator",
    "CostResult",
    "ModelComparisonRow",
    "estimate_cost",
    "compare_models",
    "RepositoryPacker",
    "PackResult",
    "pack_repository",
    "BudgetGuard",
    "GuardResult",
    "check_budget",
]
