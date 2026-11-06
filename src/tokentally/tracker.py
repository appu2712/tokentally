"""
Session-level cost tracking context manager and Python function decorators.
"""

from dataclasses import dataclass, field
import functools
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Union

from .counter import count_tokens
from .calculator import estimate_cost, CostResult


class BudgetExceededError(RuntimeError):
    """Raised when an operation or session exceeds the specified budget."""
    pass


@dataclass
class CallRecord:
    timestamp: float
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float
    duration_sec: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class BudgetTracker:
    """
    Thread-safe context manager to aggregate multi-call LLM spend in a session.
    """

    def __init__(self, max_budget_usd: Optional[float] = None, name: str = "default_session"):
        self.max_budget_usd = max_budget_usd
        self.name = name
        self.records: List[CallRecord] = []
        self._lock = threading.RLock()
        self._start_time: float = 0.0

    def __enter__(self):
        self._start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def record(
        self,
        prompt: Union[str, int],
        completion: Union[str, int] = "",
        model: str = "gpt-4o",
        cached_tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CostResult:
        """Record an LLM call to the tracker."""
        t0 = time.time()
        in_tok = prompt if isinstance(prompt, int) else count_tokens(prompt, model=model)
        out_tok = completion if isinstance(completion, int) else count_tokens(completion, model=model)

        cost_res = estimate_cost(
            in_tok, model=model, completion_tokens=out_tok, cached_tokens=cached_tokens
        )

        with self._lock:
            self.records.append(
                CallRecord(
                    timestamp=t0,
                    model=cost_res.model,
                    input_tokens=in_tok,
                    output_tokens=out_tok,
                    total_tokens=cost_res.total_tokens,
                    cost_usd=cost_res.total_cost_usd,
                    duration_sec=time.time() - t0,
                    metadata=metadata or {},
                )
            )

            current_total = self.total_cost_usd
            if self.max_budget_usd is not None and current_total > self.max_budget_usd:
                raise BudgetExceededError(
                    f"Session budget of ${self.max_budget_usd:.4f} exceeded! Current total spend: ${current_total:.6f}"
                )

        return cost_res

    @property
    def total_cost_usd(self) -> float:
        with self._lock:
            return round(sum(r.cost_usd for r in self.records), 8)

    @property
    def total_tokens(self) -> int:
        with self._lock:
            return sum(r.total_tokens for r in self.records)

    @property
    def call_count(self) -> int:
        with self._lock:
            return len(self.records)

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            by_model: Dict[str, Dict[str, Any]] = {}
            for r in self.records:
                if r.model not in by_model:
                    by_model[r.model] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
                by_model[r.model]["calls"] += 1
                by_model[r.model]["tokens"] += r.total_tokens
                by_model[r.model]["cost_usd"] += r.cost_usd

            return {
                "session_name": self.name,
                "total_calls": len(self.records),
                "total_tokens": sum(r.total_tokens for r in self.records),
                "total_cost_usd": round(sum(r.cost_usd for r in self.records), 6),
                "breakdown_by_model": by_model,
            }


def track(model: str = "gpt-4o", max_cost_usd: Optional[float] = None) -> Callable:
    """
    Decorator for Python functions that return strings or dictionaries from LLMs.
    Logs execution cost and validates against budget thresholds.
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            res = fn(*args, **kwargs)
            text_repr = str(res)
            tokens = count_tokens(text_repr, model=model)
            cost = estimate_cost(tokens, model=model).total_cost_usd

            if max_cost_usd is not None and cost > max_cost_usd:
                raise BudgetExceededError(
                    f"Function '{fn.__name__}' returned {tokens:,} tokens (${cost:.6f}), exceeding limit of ${max_cost_usd:.4f}"
                )
            return res
        return wrapper
    return decorator
