"""
Automated token and cost regression comparator.
Compares a candidate prompt against a stored baseline or historical version,
calculating token inflation, monthly cost projections, and failing CI on budget violations.
"""

from dataclasses import dataclass, asdict
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .counter import count_tokens_detailed
from .calculator import estimate_cost


@dataclass
class RegressionResult:
    baseline_tokens: int
    candidate_tokens: int
    delta_tokens: int
    percent_change: float
    baseline_cost_usd: float
    candidate_cost_usd: float
    delta_cost_usd: float
    projected_monthly_impact_10k_usd: float
    is_regression: bool
    is_violation: bool
    max_allowed_pct: float
    model: str
    message: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _looks_like_file_path(target: str) -> bool:
    if not target or "\n" in target:
        return False
    p = target.strip()
    if p.startswith(("./", "../", "/", "\\", "~")) or (len(p) > 2 and p[1] == ":" and p[2] in ("/", "\\")):
        return True
    file_exts = {".txt", ".md", ".json", ".xml", ".prompt", ".py", ".ts", ".js", ".csv", ".toml", ".yaml", ".yml", ".html"}
    return any(p.lower().endswith(ext) for ext in file_exts)


def _load_text_or_path(target: Union[str, Path]) -> str:
    target_str = str(target)

    # Check if target is a git revision reference, e.g. "git:main:prompts/system.txt"
    if target_str.startswith("git:"):
        parts = target_str.split(":", 2)
        if len(parts) == 3:
            _, git_ref, git_path = parts
            try:
                import subprocess
                cmd = ["git", "show", f"{git_ref}:{git_path}"]
                res = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding="utf-8",
                    errors="replace",
                )
                return res.stdout
            except Exception as e:
                raise RuntimeError(f"Failed to fetch git revision '{git_ref}:{git_path}': {e}")

    if os.path.isfile(target_str):
        with open(target_str, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    if _looks_like_file_path(target_str) and not os.path.exists(target_str):
        raise FileNotFoundError(f"Target file not found: '{target_str}'")
    return target_str


class RegressionComparator:
    """Evaluates prompt inflation between baseline and candidate revisions."""

    def __init__(self):
        pass

    def compare(
        self,
        baseline: Union[str, Path],
        candidate: Union[str, Path],
        model: str = "gpt-4o",
        max_regression_pct: float = 15.0,
    ) -> RegressionResult:
        base_text = _load_text_or_path(baseline)
        cand_text = _load_text_or_path(candidate)

        base_cnt = count_tokens_detailed(base_text, model=model).tokens
        cand_cnt = count_tokens_detailed(cand_text, model=model).tokens

        delta_tokens = cand_cnt - base_cnt
        pct_change = ((delta_tokens / base_cnt) * 100.0) if base_cnt > 0 else (0.0 if cand_cnt == 0 else 100.0)

        base_cost = estimate_cost(base_cnt, model=model).total_cost_usd
        cand_cost = estimate_cost(cand_cnt, model=model).total_cost_usd
        delta_cost = cand_cost - base_cost

        # Monthly impact at 10,000 monthly invocations
        monthly_impact = delta_cost * 10000.0

        is_regression = delta_tokens > 0
        is_violation = is_regression and (pct_change > max_regression_pct)

        if is_violation:
            msg = (
                f"TOKEN REGRESSION VIOLATION: Candidate prompt expanded by +{pct_change:.1f}% "
                f"(+{delta_tokens:,} tokens), exceeding allowed threshold of +{max_regression_pct:.1f}%."
            )
        elif is_regression:
            msg = f"Token growth: +{pct_change:.1f}% (+{delta_tokens:,} tokens), within allowed threshold of +{max_regression_pct:.1f}%."
        else:
            msg = f"Token savings: {pct_change:.1f}% ({delta_tokens:,} tokens). No regression."

        return RegressionResult(
            baseline_tokens=base_cnt,
            candidate_tokens=cand_cnt,
            delta_tokens=delta_tokens,
            percent_change=round(pct_change, 2),
            baseline_cost_usd=round(base_cost, 6),
            candidate_cost_usd=round(cand_cost, 6),
            delta_cost_usd=round(delta_cost, 6),
            projected_monthly_impact_10k_usd=round(monthly_impact, 2),
            is_regression=is_regression,
            is_violation=is_violation,
            max_allowed_pct=max_regression_pct,
            model=model,
            message=msg,
        )


_DEFAULT_COMPARATOR = RegressionComparator()


def compare_prompt_regression(
    baseline: Union[str, Path],
    candidate: Union[str, Path],
    model: str = "gpt-4o",
    max_regression_pct: float = 15.0,
) -> RegressionResult:
    """Convenience helper to compare candidate prompt against baseline."""
    return _DEFAULT_COMPARATOR.compare(
        baseline=baseline,
        candidate=candidate,
        model=model,
        max_regression_pct=max_regression_pct,
    )
