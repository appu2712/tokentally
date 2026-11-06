"""
Comprehensive audit and cost projection report generator (HTML, Markdown, CSV).
"""

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .counter import count_tokens
from .calculator import estimate_cost, compare_models
from .packer import pack_repository


def _looks_like_file_path(target: str) -> bool:
    if not target or "\n" in target:
        return False
    p = target.strip()
    if p.startswith(("./", "../", "/", "\\", "~")) or (len(p) > 2 and p[1] == ":" and p[2] in ("/", "\\")):
        return True
    file_exts = {".txt", ".md", ".json", ".xml", ".prompt", ".py", ".ts", ".js", ".csv", ".toml", ".yaml", ".yml", ".html"}
    return any(p.lower().endswith(ext) for ext in file_exts)


class AuditReporter:
    """Generates executive summaries, CSV matrices, and HTML cost audits."""

    def __init__(self):
        pass

    def generate_markdown(
        self,
        target_path: str,
        model: str = "gpt-4o",
        completion_tokens: int = 500,
    ) -> str:
        if os.path.isdir(target_path):
            pack_res = pack_repository(target_path, model=model)
            tokens = pack_res.total_tokens
            target_type = f"Directory ({pack_res.total_files} files)"
        elif os.path.isfile(target_path):
            tokens = count_tokens(target_path, model=model, is_file=True)
            target_type = "File"
        elif _looks_like_file_path(target_path) and not os.path.exists(target_path):
            raise FileNotFoundError(f"Target file or directory not found: '{target_path}'")
        else:
            tokens = count_tokens(target_path, model=model)
            target_type = "Text Prompt"

        cost_res = estimate_cost(tokens, model=model, completion_tokens=completion_tokens)
        comp_rows = compare_models(tokens, completion_ratio=(completion_tokens / tokens) if tokens > 0 else 0.5)

        lines = [
            f"# 📊 TokenTally Audit Report",
            f"- **Target**: `{target_path}` ({target_type})",
            f"- **Input Tokens**: {cost_res.input_tokens:,}",
            f"- **Estimated Output Tokens**: {cost_res.output_tokens:,}",
            f"- **Total Tokens per Call**: {cost_res.total_tokens:,}",
            f"- **Primary Evaluated Model**: `{model}` (${cost_res.total_cost_usd:.6f} / call)",
            "",
            "## 📈 Volume Projections",
            "| Monthly Volume | Estimated Invocations | Total Monthly Spend (USD) |",
            "| :--- | :--- | :--- |",
            f"| Low Volume | 1,000 calls | ${cost_res.total_cost_usd * 1_000:,.2f} |",
            f"| Moderate Volume | 10,000 calls | ${cost_res.total_cost_usd * 10_000:,.2f} |",
            f"| Production Scale | 100,000 calls | ${cost_res.total_cost_usd * 100_000:,.2f} |",
            f"| Enterprise Scale | 1,000,000 calls | ${cost_res.total_cost_usd * 1_000_000:,.2f} |",
            "",
            "## 🤖 Cross-Model Cost Matrix",
            "| Model | Provider | Cost / Call (USD) | Cost / 10k Calls | Relative Ratio |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]

        for r in comp_rows:
            lines.append(
                f"| **{r.model}** | {r.provider} | ${r.total_cost_usd:.6f} | ${r.total_cost_usd * 10_000:,.2f} | `{r.relative_ratio:.2f}x` |"
            )

        return "\n".join(lines)

    def generate_csv(
        self,
        target_path: str,
        completion_tokens: int = 500,
    ) -> str:
        if os.path.isdir(target_path):
            tokens = pack_repository(target_path).total_tokens
        elif os.path.isfile(target_path):
            tokens = count_tokens(target_path, is_file=True)
        elif _looks_like_file_path(target_path) and not os.path.exists(target_path):
            raise FileNotFoundError(f"Target file or directory not found: '{target_path}'")
        else:
            tokens = count_tokens(target_path)

        rows = compare_models(tokens)
        lines = ["model,provider,input_tokens,output_tokens,cost_per_call_usd,cost_per_10k_calls_usd,ratio"]
        for r in rows:
            lines.append(
                f"{r.model},{r.provider},{r.input_tokens},{r.output_tokens},{r.total_cost_usd:.8f},{r.total_cost_usd * 10_000:.4f},{r.relative_ratio}"
            )
        return "\n".join(lines)


_DEFAULT_REPORTER = AuditReporter()


def generate_report(
    target_path: str,
    output_format: str = "markdown",
    model: str = "gpt-4o",
    completion_tokens: int = 500,
) -> str:
    """Convenience helper to generate audit reports."""
    if output_format.lower() == "csv":
        return _DEFAULT_REPORTER.generate_csv(target_path, completion_tokens=completion_tokens)
    return _DEFAULT_REPORTER.generate_markdown(
        target_path, model=model, completion_tokens=completion_tokens
    )
