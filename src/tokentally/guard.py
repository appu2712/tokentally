"""
CI/CD Budget Guardrail and pre-commit checks for LLM costs and token counts.
"""

from dataclasses import dataclass, asdict
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .counter import count_tokens
from .calculator import estimate_cost
from .packer import pack_repository


@dataclass
class GuardResult:
    passed: bool
    violations: List[str]
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
    """Evaluates targets against specified spending and token constraints."""

    def __init__(self):
        pass

    def check(
        self,
        target: Union[str, Path],
        model: str = "gpt-4o",
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        completion_tokens: int = 0,
    ) -> GuardResult:
        """
        Check target against specified limits.
        'target' can be a file path, directory path, or raw string prompt.
        """
        target_str = str(target)
        violations: List[str] = []

        # Determine target type
        if os.path.isdir(target_str):
            pack_res = pack_repository(target_str, model=model)
            tokens = pack_res.total_tokens
        elif os.path.isfile(target_str):
            tokens = count_tokens(target_str, model=model, is_file=True)
        else:
            tokens = count_tokens(target_str, model=model)

        cost_res = estimate_cost(tokens, model=model, completion_tokens=completion_tokens)
        cost_usd = cost_res.total_cost_usd

        if max_tokens is not None and tokens > max_tokens:
            violations.append(
                f"Token count violation: {tokens:,} tokens exceeds maximum threshold of {max_tokens:,} tokens."
            )

        if max_cost_usd is not None and cost_usd > max_cost_usd:
            violations.append(
                f"Cost limit violation: estimated ${cost_usd:.6f} exceeds limit of ${max_cost_usd:.4f} for model '{model}'."
            )

        return GuardResult(
            passed=len(violations) == 0,
            violations=violations,
            tokens=tokens,
            cost_usd=cost_usd,
            model=model,
            target=target_str,
        )


_DEFAULT_GUARD = BudgetGuard()


def check_budget(
    target: Union[str, Path],
    model: str = "gpt-4o",
    max_cost_usd: Optional[float] = None,
    max_tokens: Optional[int] = None,
    completion_tokens: int = 0,
) -> GuardResult:
    """Convenience helper to check target against constraints."""
    return _DEFAULT_GUARD.check(
        target=target,
        model=model,
        max_cost_usd=max_cost_usd,
        max_tokens=max_tokens,
        completion_tokens=completion_tokens,
    )
