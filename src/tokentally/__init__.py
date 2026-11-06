"""
tokentally - Fast Token Counter, LLM Cost Estimator & Context Optimization Engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The unified AI Resource Optimization Layer:
Token counting, multi-model cost modeling, context layer decomposition,
git review value density profiling, prompt optimization with constraint invariance,
regression gates, tool schema auditing, and native MCP intelligence.
"""

from .models import (
    MODEL_REGISTRY,
    ModelPricing,
    get_model_pricing,
    list_supported_models,
)
from .counter import (
    TokenCounter,
    TokenCountResult,
    count_tokens,
    count_tokens_detailed,
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
    TransformationStep,
    optimize_prompt,
)
from .git import (
    GitDiffProfiler,
    GitDiffResult,
    FileDiffStat,
    classify_diff_file,
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
from .analyzer import (
    PromptContextAnalyzer,
    PromptAnalysisResult,
    ContextComponent,
    CacheabilityReport,
    ReasoningTokenAnalysis,
    analyze_prompt_context,
)
from .regression import (
    RegressionComparator,
    RegressionResult,
    compare_prompt_regression,
)
from .tools import (
    ToolWorkloadEngine,
    ToolCatalogReport,
    ToolSchemaStat,
    HistorySimulationResult,
    AgentLoopReport,
    analyze_tool_schemas,
    simulate_history_growth,
)
from .config import (
    TokentallyConfig,
    BudgetConfig,
    RegressionConfig,
    ReviewConfig,
    load_config,
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
    "TokenCountResult",
    "count_tokens",
    "count_tokens_detailed",
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
    "TransformationStep",
    "optimize_prompt",
    "GitDiffProfiler",
    "GitDiffResult",
    "FileDiffStat",
    "classify_diff_file",
    "profile_git_diff",
    "BudgetTracker",
    "BudgetExceededError",
    "track",
    "AuditReporter",
    "generate_report",
    "PromptContextAnalyzer",
    "PromptAnalysisResult",
    "ContextComponent",
    "CacheabilityReport",
    "ReasoningTokenAnalysis",
    "analyze_prompt_context",
    "RegressionComparator",
    "RegressionResult",
    "compare_prompt_regression",
    "ToolWorkloadEngine",
    "ToolCatalogReport",
    "ToolSchemaStat",
    "HistorySimulationResult",
    "AgentLoopReport",
    "analyze_tool_schemas",
    "simulate_history_growth",
    "TokentallyConfig",
    "BudgetConfig",
    "RegressionConfig",
    "ReviewConfig",
    "load_config",
    "MCPServer",
    "scaffold_github_workflow",
    "install_git_precommit_hook",
]
