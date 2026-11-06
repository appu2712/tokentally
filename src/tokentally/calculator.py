"""
Accurate cost estimation and comparative analysis across models.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Union

from .models import get_model_pricing, list_supported_models, normalize_model_name
from .counter import count_tokens


@dataclass
class CostResult:
    """Detailed cost breakdown for a model invocation."""
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    cached_tokens: int
    total_tokens: int
    input_cost_usd: float
    output_cost_usd: float
    cached_cost_usd: float
    total_cost_usd: float
    is_inferred: bool = False
    inference_notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def formatted_total(self) -> str:
        """Formatted USD string (e.g. '$0.002450')."""
        if self.total_cost_usd < 0.01:
            return f"${self.total_cost_usd:.6f}"
        return f"${self.total_cost_usd:.4f}"


@dataclass
class ModelComparisonRow:
    """Row for multi-model comparison tables."""
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost_usd: float
    relative_ratio: float  # e.g. 1.0x (baseline), 0.15x (cheaper), etc.

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostCalculator:
    """Calculates LLM inference cost based on token counts and up-to-date pricing."""

    def __init__(self):
        pass

    def estimate(
        self,
        prompt: Union[str, int],
        model: str = "gpt-4o",
        completion_tokens: int = 0,
        cached_tokens: int = 0,
    ) -> CostResult:
        """
        Estimate the dollar cost for a prompt and expected completion.
        'prompt' can either be an input string or an already counted integer of tokens.
        """
        canonical_name = normalize_model_name(model)
        pricing = get_model_pricing(canonical_name)

        if isinstance(prompt, int):
            raw_input_tokens = max(0, prompt)
        else:
            raw_input_tokens = count_tokens(prompt, model=canonical_name)

        # Handle cached tokens
        cached_tokens = min(raw_input_tokens, max(0, cached_tokens))
        billable_input_tokens = raw_input_tokens - cached_tokens

        # Calculate costs (per million tokens)
        input_cost = (billable_input_tokens / 1_000_000.0) * pricing.input_per_m

        if pricing.cached_input_per_m is not None:
            cached_cost = (cached_tokens / 1_000_000.0) * pricing.cached_input_per_m
        else:
            cached_cost = (cached_tokens / 1_000_000.0) * pricing.input_per_m

        output_cost = (max(0, completion_tokens) / 1_000_000.0) * pricing.output_per_m
        total_cost = input_cost + cached_cost + output_cost

        return CostResult(
            model=canonical_name,
            provider=pricing.provider,
            input_tokens=raw_input_tokens,
            output_tokens=max(0, completion_tokens),
            cached_tokens=cached_tokens,
            total_tokens=raw_input_tokens + max(0, completion_tokens),
            input_cost_usd=round(input_cost, 8),
            output_cost_usd=round(output_cost, 8),
            cached_cost_usd=round(cached_cost, 8),
            total_cost_usd=round(total_cost, 8),
            is_inferred=pricing.is_inferred,
            inference_notes=pricing.inference_rationale,
        )

    def compare(
        self,
        prompt: Union[str, int],
        models: Optional[List[str]] = None,
        completion_ratio: float = 0.5,
        baseline_model: str = "gpt-4o",
    ) -> List[ModelComparisonRow]:
        """
        Compare the cost of running a prompt across multiple models.
        'completion_ratio' specifies estimated output tokens as a fraction of input tokens.
        """
        if models is None:
            models = [
                "gpt-4o",
                "gpt-4o-mini",
                "o3-mini",
                "o1",
                "claude-3-7-sonnet",
                "claude-3-5-sonnet",
                "claude-3-5-haiku",
                "gemini-2.5-pro",
                "gemini-2.5-flash",
                "deepseek-v3",
                "deepseek-r1",
            ]

        # First calculate for the baseline model
        base_name = normalize_model_name(baseline_model)
        if isinstance(prompt, int):
            tokens = prompt
        else:
            tokens = count_tokens(prompt, model=base_name)

        comp_tokens = int(tokens * completion_ratio)
        base_cost_res = self.estimate(tokens, model=base_name, completion_tokens=comp_tokens)
        base_cost = base_cost_res.total_cost_usd or 0.000001

        rows: List[ModelComparisonRow] = []
        for m in models:
            try:
                res = self.estimate(tokens, model=m, completion_tokens=comp_tokens)
                ratio = res.total_cost_usd / base_cost
                rows.append(
                    ModelComparisonRow(
                        model=res.model,
                        provider=res.provider,
                        input_tokens=res.input_tokens,
                        output_tokens=res.output_tokens,
                        total_tokens=res.total_tokens,
                        total_cost_usd=res.total_cost_usd,
                        relative_ratio=round(ratio, 3),
                    )
                )
            except KeyError:
                continue

        # Sort by total cost ascending
        rows.sort(key=lambda r: r.total_cost_usd)
        return rows


_DEFAULT_CALCULATOR = CostCalculator()


def estimate_cost(
    prompt: Union[str, int],
    model: str = "gpt-4o",
    completion_tokens: int = 0,
    cached_tokens: int = 0,
) -> CostResult:
    """Convenience helper to estimate cost for a prompt."""
    return _DEFAULT_CALCULATOR.estimate(
        prompt, model=model, completion_tokens=completion_tokens, cached_tokens=cached_tokens
    )


def compare_models(
    prompt: Union[str, int],
    models: Optional[List[str]] = None,
    completion_ratio: float = 0.5,
) -> List[ModelComparisonRow]:
    """Convenience helper to compare cost across multiple models."""
    return _DEFAULT_CALCULATOR.compare(
        prompt, models=models, completion_ratio=completion_ratio
    )
