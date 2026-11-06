"""
Prompt and code context optimizer / minifier to reduce token waste and save API costs.
"""

from dataclasses import dataclass, asdict
import re
from typing import Any, Dict, Optional

from .counter import count_tokens
from .calculator import estimate_cost


@dataclass
class OptimizationResult:
    original_tokens: int
    optimized_tokens: int
    saved_tokens: int
    percent_reduction: float
    original_cost_usd: float
    optimized_cost_usd: float
    saved_cost_usd: float
    model: str
    original_length: int
    optimized_length: int
    optimized_text: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        del d["optimized_text"]
        return d


class PromptOptimizer:
    """Intelligently cleans and shrinks prompts without losing structural semantic meaning."""

    def __init__(self):
        pass

    def optimize(
        self,
        text: str,
        model: str = "gpt-4o",
        strip_comments: bool = False,
        normalize_whitespace: bool = True,
        max_consecutive_newlines: int = 1,
    ) -> OptimizationResult:
        if not text:
            return OptimizationResult(
                original_tokens=0,
                optimized_tokens=0,
                saved_tokens=0,
                percent_reduction=0.0,
                original_cost_usd=0.0,
                optimized_cost_usd=0.0,
                saved_cost_usd=0.0,
                model=model,
                original_length=0,
                optimized_length=0,
                optimized_text="",
            )

        orig_len = len(text)
        orig_tokens = count_tokens(text, model=model)
        orig_cost = estimate_cost(orig_tokens, model=model).total_cost_usd

        result = text

        # Strip full-line comments if requested (# in python/shell or // in JS/C)
        if strip_comments:
            result = re.sub(r"^\s*(#|//)\s*.*?$", "", result, flags=re.MULTILINE)

        if normalize_whitespace:
            # Strip trailing whitespace on each line
            lines = [line.rstrip() for line in result.splitlines()]
            result = "\n".join(lines)

            # Collapse 3+ consecutive newlines to max_consecutive_newlines
            nl_pattern = r"\n{" + str(max_consecutive_newlines + 1) + r",}"
            replacement = "\n" * max_consecutive_newlines
            result = re.sub(nl_pattern, replacement, result)

            # Strip leading and trailing document whitespace
            result = result.strip()

        opt_len = len(result)
        opt_tokens = count_tokens(result, model=model)
        opt_cost = estimate_cost(opt_tokens, model=model).total_cost_usd

        saved_tok = max(0, orig_tokens - opt_tokens)
        pct_saved = (saved_tok / orig_tokens * 100.0) if orig_tokens > 0 else 0.0
        saved_cost = max(0.0, orig_cost - opt_cost)

        return OptimizationResult(
            original_tokens=orig_tokens,
            optimized_tokens=opt_tokens,
            saved_tokens=saved_tok,
            percent_reduction=round(pct_saved, 2),
            original_cost_usd=round(orig_cost, 8),
            optimized_cost_usd=round(opt_cost, 8),
            saved_cost_usd=round(saved_cost, 8),
            model=model,
            original_length=orig_len,
            optimized_length=opt_len,
            optimized_text=result,
        )


_DEFAULT_OPTIMIZER = PromptOptimizer()


def optimize_prompt(
    text: str,
    model: str = "gpt-4o",
    strip_comments: bool = False,
    normalize_whitespace: bool = True,
    max_consecutive_newlines: int = 1,
) -> OptimizationResult:
    """Convenience helper to optimize and shrink a prompt."""
    return _DEFAULT_OPTIMIZER.optimize(
        text=text,
        model=model,
        strip_comments=strip_comments,
        normalize_whitespace=normalize_whitespace,
        max_consecutive_newlines=max_consecutive_newlines,
    )
