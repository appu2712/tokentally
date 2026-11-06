"""
Project configuration loader for tokentally.toml.
Provides zero-dependency declarative policies for budgets, regression thresholds, and code review rules.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Use standard library tomllib in Python 3.11+
try:
    import tomllib
    _HAS_TOMLLIB = True
except ImportError:
    tomllib = None  # type: ignore
    _HAS_TOMLLIB = False


def _parse_simple_toml(content: str) -> Dict[str, Any]:
    """Lightweight zero-dependency TOML parser for standard sections and key-values."""
    result: Dict[str, Any] = {}
    current_section = ""

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1].strip()
            if current_section not in result:
                result[current_section] = {}
            continue

        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            # Parse types
            parsed_val: Any = val
            if val.lower() == "true":
                parsed_val = True
            elif val.lower() == "false":
                parsed_val = False
            else:
                try:
                    if "." in val:
                        parsed_val = float(val)
                    else:
                        parsed_val = int(val)
                except ValueError:
                    parsed_val = val

            if current_section:
                result[current_section][key] = parsed_val
            else:
                result[key] = parsed_val

    return result


@dataclass
class BudgetConfig:
    max_prompt_tokens: Optional[int] = None
    max_cost_per_request: Optional[float] = None
    warning_cost_usd: Optional[float] = None
    default_model: str = "gpt-4o"


@dataclass
class RegressionConfig:
    baseline_file: Optional[str] = None
    max_regression_pct: float = 15.0
    fail_on_regression: bool = True


@dataclass
class ReviewConfig:
    max_review_tokens: Optional[int] = 50000
    exclude_lockfiles: bool = True
    exclude_generated: bool = True


@dataclass
class TokentallyConfig:
    budget: BudgetConfig = field(default_factory=BudgetConfig)
    regression: RegressionConfig = field(default_factory=RegressionConfig)
    review: ReviewConfig = field(default_factory=ReviewConfig)
    custom_models: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    config_path: Optional[str] = None


def load_config(root_dir: Optional[str] = None) -> TokentallyConfig:
    """Find and load tokentally.toml if present, or return defaults."""
    start = Path(root_dir or os.getcwd()).resolve()

    # Search current directory and up to 2 parent directories
    candidates = [
        start / "tokentally.toml",
        start.parent / "tokentally.toml",
        start.parent.parent / "tokentally.toml",
    ]

    cfg_file = next((c for c in candidates if c.is_file()), None)
    if not cfg_file:
        return TokentallyConfig()

    try:
        content = cfg_file.read_text(encoding="utf-8")
        if _HAS_TOMLLIB and tomllib is not None:
            raw = tomllib.loads(content)
        else:
            raw = _parse_simple_toml(content)

        budget_raw = raw.get("budget", {})
        budget = BudgetConfig(
            max_prompt_tokens=budget_raw.get("max_prompt_tokens"),
            max_cost_per_request=budget_raw.get("max_cost_per_request"),
            warning_cost_usd=budget_raw.get("warning_cost_usd"),
            default_model=budget_raw.get("default_model", "gpt-4o"),
        )

        reg_raw = raw.get("regression", {})
        regression = RegressionConfig(
            baseline_file=reg_raw.get("baseline_file"),
            max_regression_pct=float(reg_raw.get("max_regression_pct", 15.0)),
            fail_on_regression=reg_raw.get("fail_on_regression", True),
        )

        rev_raw = raw.get("review", {})
        review = ReviewConfig(
            max_review_tokens=rev_raw.get("max_review_tokens", 50000),
            exclude_lockfiles=rev_raw.get("exclude_lockfiles", True),
            exclude_generated=rev_raw.get("exclude_generated", True),
        )

        custom_models: Dict[str, Dict[str, Any]] = {}
        if "custom_models" in raw and isinstance(raw["custom_models"], dict):
            custom_models = raw["custom_models"]
        # Handle flattened sections from simple parser, e.g. "custom_models.my_model"
        for k, v in raw.items():
            if k.startswith("custom_models.") and isinstance(v, dict):
                m_name = k.split(".", 1)[1]
                custom_models[m_name] = v

        return TokentallyConfig(
            budget=budget,
            regression=regression,
            review=review,
            custom_models=custom_models,
            config_path=str(cfg_file),
        )
    except Exception:
        return TokentallyConfig()
