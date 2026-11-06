"""
tokentally - Fast Token Counter, LLM Cost Estimator & Context Packer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A unified developer library and CLI to count tokens, estimate exact multi-model costs,
pack repositories for LLM prompts, enforce CI/CD budget guardrails, optimize prompts,
profile git diffs, and host local studio dashboards across OpenAI, Claude, Gemini,
DeepSeek, Mistral, and local open-source models.
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
from .optimizer import (
    PromptOptimizer,
    OptimizationResult,
    optimize_prompt,
)
from .git import (
    GitDiffProfiler,
    GitDiffResult,
    profile_git_diff,
)
from .tracker import (
    BudgetTracker,
    BudgetExceededError,
    track,
)
from .reporter import (
    AuditReporter,
    generate_report,
)
from .mcp import (
    MCPServer,
)
from .hooks import (
    scaffold_github_workflow,
    install_git_precommit_hook,
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
    "PromptOptimizer",
    "OptimizationResult",
    "optimize_prompt",
    "GitDiffProfiler",
    "GitDiffResult",
    "profile_git_diff",
    "BudgetTracker",
    "BudgetExceededError",
    "track",
    "AuditReporter",
    "generate_report",
    "MCPServer",
    "scaffold_github_workflow",
    "install_git_precommit_hook",
]
