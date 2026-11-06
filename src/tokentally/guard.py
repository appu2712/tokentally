"""
CI/CD Budget Guardrail with warning thresholds, tolerance margins, and tokentally.toml integration.
"""

from dataclasses import dataclass, asdict
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .counter import count_tokens_detailed
from .calculator import estimate_cost
from .packer import pack_repository
from .config import load_config


@dataclass
class GuardResult:
    passed: bool
    has_warnings: bool
    violations: List[str]
    warnings: List[str]
    tokens: int
    cost_usd: float
    model: str
    target: str

    @property
    def exit_code(self) -> int:
        return 0 if self.passed else 1

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BudgetGuard:
    """Evaluates targets against specified spending and token constraints with soft warnings and hard gates."""

    def __init__(self):
        pass

    def check(
        self,
        target: Union[str, Path],
        model: Optional[str] = None,
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        warning_cost_usd: Optional[float] = None,
        completion_tokens: int = 0,
    ) -> GuardResult:
        cfg = load_config()

        # Resolve model
        eval_model = model or cfg.budget.default_model

        # Resolve limits (explicit CLI flag takes precedence over tokentally.toml)
        eff_max_tokens = max_tokens if max_tokens is not None else cfg.budget.max_prompt_tokens
        eff_max_cost = max_cost_usd if max_cost_usd is not None else cfg.budget.max_cost_per_request
        eff_warn_cost = warning_cost_usd if warning_cost_usd is not None else cfg.budget.warning_cost_usd

        target_str = str(target)
        violations: List[str] = []
        warnings: List[str] = []

        # Determine target type
        if os.path.isdir(target_str):
            pack_res = pack_repository(target_str, model=eval_model)
            tokens = pack_res.total_tokens
        elif os.path.isfile(target_str):
            tokens = count_tokens_detailed(target_str, model=eval_model, is_file=True).tokens
        else:
            tokens = count_tokens_detailed(target_str, model=eval_model).tokens

        cost_res = estimate_cost(tokens, model=eval_model, completion_tokens=completion_tokens)
        cost_usd = cost_res.total_cost_usd

        # Check hard violations
        if eff_max_tokens is not None and tokens > eff_max_tokens:
            violations.append(
                f"Token count violation: {tokens:,} tokens exceeds maximum threshold of {eff_max_tokens:,} tokens."
            )

        if eff_max_cost is not None and cost_usd > eff_max_cost:
            violations.append(
                f"Cost limit violation: estimated ${cost_usd:.6f} exceeds limit of ${eff_max_cost:.4f} for model '{eval_model}'."
            )

        # Check soft warnings (does not cause build failure)
        if eff_warn_cost is not None and cost_usd > eff_warn_cost and not violations:
            warnings.append(
                f"Budget Warning: estimated spend ${cost_usd:.6f} exceeds warning threshold of ${eff_warn_cost:.4f}."
            )

        return GuardResult(
            passed=len(violations) == 0,
            has_warnings=len(warnings) > 0,
            violations=violations,
            warnings=warnings,
            tokens=tokens,
            cost_usd=cost_usd,
            model=eval_model,
            target=target_str,
        )


_DEFAULT_GUARD = BudgetGuard()


def check_budget(
    target: Union[str, Path],
    model: Optional[str] = None,
    max_cost_usd: Optional[float] = None,
    max_tokens: Optional[int] = None,
    warning_cost_usd: Optional[float] = None,
    completion_tokens: int = 0,
) -> GuardResult:
    """Convenience helper to check target against constraints."""
    return _DEFAULT_GUARD.check(
        target=target,
        model=model,
        max_cost_usd=max_cost_usd,
        max_tokens=max_tokens,
        warning_cost_usd=warning_cost_usd,
        completion_tokens=completion_tokens,
    )
