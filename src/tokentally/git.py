"""
Git diff token analyzer, generated-code classifier, and review value density profiler.
"""

from dataclasses import dataclass, asdict
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Dict, List, Optional

from .counter import count_tokens
from .calculator import estimate_cost


LOCKFILE_NAMES = {
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "bun.lock",
    "poetry.lock",
    "pipfile.lock",
    "cargo.lock",
    "composer.lock",
    "gemfile.lock",
    "go.sum",
    "flake.lock",
}

GENERATED_PATTERNS = [
    re.compile(r"\.min\.(js|css)$", re.IGNORECASE),
    re.compile(r"\.bundle\.(js|css)$", re.IGNORECASE),
    re.compile(r"\.generated\.", re.IGNORECASE),
    re.compile(r"_pb2(_grpc)?\.py$", re.IGNORECASE),
    re.compile(r"\.pb\.go$", re.IGNORECASE),
    re.compile(r"openapi\.(json|yaml)$", re.IGNORECASE),
    re.compile(r"swagger\.(json|yaml)$", re.IGNORECASE),
    re.compile(r"schema\.graphql$", re.IGNORECASE),
]

DOC_EXTENSIONS = {".md", ".rst", ".txt", ".adoc"}
FIXTURE_DIR_NAMES = {"fixtures", "testdata", "snapshots", "__snapshots__"}


def classify_diff_file(path_str: str) -> str:
    """Classify file into human_code, lockfile, generated, fixture, docs, or binary."""
    p = Path(path_str)
    filename = p.name.lower()

    if filename in LOCKFILE_NAMES:
        return "lockfile"

    for pat in GENERATED_PATTERNS:
        if pat.search(filename):
            return "generated"

    for part in p.parts:
        if part.lower() in FIXTURE_DIR_NAMES:
            return "fixture"

    if p.suffix.lower() in DOC_EXTENSIONS:
        return "docs"

    return "human_code"


@dataclass
class FileDiffStat:
    path: str
    tokens: int
    added_lines: int
    deleted_lines: int
    category: str
    is_generated: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GitDiffResult:
    target_ref: str
    total_tokens: int
    files_changed: int
    human_code_tokens: int
    generated_tokens: int
    review_value_density: float  # Human code tokens / Total tokens (0.0 to 1.0)
    estimated_review_cost_usd: float
    optimized_review_cost_usd: float
    potential_savings_pct: float
    model: str
    file_breakdown: List[FileDiffStat]
    recommendations: List[str]
    raw_diff: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_ref": self.target_ref,
            "total_tokens": self.total_tokens,
            "files_changed": self.files_changed,
            "human_code_tokens": self.human_code_tokens,
            "generated_tokens": self.generated_tokens,
            "review_value_density": self.review_value_density,
            "estimated_review_cost_usd": self.estimated_review_cost_usd,
            "optimized_review_cost_usd": self.optimized_review_cost_usd,
            "potential_savings_pct": self.potential_savings_pct,
            "model": self.model,
            "recommendations": self.recommendations,
            "file_breakdown": [f.to_dict() for f in self.file_breakdown],
        }


class GitDiffProfiler:
    """Calculates token weight, review value density, and code review costs of git changes."""

    def __init__(self, repo_dir: Optional[str] = None):
        self.repo_dir = repo_dir or os.getcwd()

    def _run_git(self, args: List[str]) -> str:
        try:
            cmd = ["git"] + args
            res = subprocess.run(
                cmd,
                cwd=self.repo_dir,
                capture_output=True,
                text=True,
                check=True,
                encoding="utf-8",
                errors="replace",
            )
            return res.stdout
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(f"Git execution failed: {e}")

    def profile_diff(
        self,
        ref: Optional[str] = None,
        staged: bool = False,
        model: str = "gpt-4o",
        raw_patch: Optional[str] = None,
        exclude_generated: bool = False,
    ) -> GitDiffResult:
        if raw_patch is not None:
            diff_text = raw_patch
            ref_label = "stdin-patch"
        else:
            args = ["diff"]
            if staged:
                args.append("--cached")
            if ref:
                args.append(ref)
            ref_label = ref or ("staged" if staged else "working-tree")
            diff_text = self._run_git(args)

        # Parse individual file changes from git diff output
        file_stats: List[FileDiffStat] = []
        chunks = diff_text.split("diff --git ")

        human_tokens = 0
        gen_tokens = 0
        filtered_chunks: List[str] = []

        for chunk in chunks:
            if not chunk.strip():
                continue
            lines = chunk.splitlines()
            first_line = lines[0] if lines else ""
            # e.g. "a/src/main.py b/src/main.py"
            parts = first_line.split(" ")
            filepath = parts[-1].lstrip("b/") if parts else "unknown"

            cat = classify_diff_file(filepath)
            is_gen = cat in ("lockfile", "generated", "fixture")

            added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
            deleted = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
            chunk_tokens = count_tokens(chunk, model=model)

            if is_gen:
                gen_tokens += chunk_tokens
            else:
                human_tokens += chunk_tokens
                filtered_chunks.append("diff --git " + chunk)

            file_stats.append(
                FileDiffStat(
                    path=filepath,
                    tokens=chunk_tokens,
                    added_lines=added,
                    deleted_lines=deleted,
                    category=cat,
                    is_generated=is_gen,
                )
            )

        total_tokens = human_tokens + gen_tokens
        density = (human_tokens / total_tokens) if total_tokens > 0 else 1.0

        full_review_cost = estimate_cost(total_tokens, model=model, completion_tokens=500).total_cost_usd
        optimized_review_cost = estimate_cost(human_tokens, model=model, completion_tokens=500).total_cost_usd

        savings_pct = ((full_review_cost - optimized_review_cost) / full_review_cost * 100.0) if full_review_cost > 0 else 0.0

        recommendations: List[str] = []
        if gen_tokens > 1000:
            recommendations.append(
                f"Generated files and lockfiles consume {gen_tokens:,} tokens ({round((1 - density) * 100, 1)}% of review context). "
                f"Excluding them will save approximately ${full_review_cost - optimized_review_cost:.6f} per review pass."
            )

        final_diff = "\n".join(filtered_chunks) if exclude_generated else diff_text
        effective_tokens = human_tokens if exclude_generated else total_tokens
        effective_cost = optimized_review_cost if exclude_generated else full_review_cost

        return GitDiffResult(
            target_ref=ref_label,
            total_tokens=effective_tokens,
            files_changed=len(file_stats),
            human_code_tokens=human_tokens,
            generated_tokens=gen_tokens,
            review_value_density=round(density, 3),
            estimated_review_cost_usd=round(effective_cost, 6),
            optimized_review_cost_usd=round(optimized_review_cost, 6),
            potential_savings_pct=round(savings_pct, 1),
            model=model,
            file_breakdown=file_stats,
            recommendations=recommendations,
            raw_diff=final_diff,
        )


_DEFAULT_GIT_PROFILER = GitDiffProfiler()


def profile_git_diff(
    ref: Optional[str] = None,
    staged: bool = False,
    model: str = "gpt-4o",
    raw_patch: Optional[str] = None,
    exclude_generated: bool = False,
) -> GitDiffResult:
    """Convenience helper to profile git diff with generated file classification."""
    return _DEFAULT_GIT_PROFILER.profile_diff(
        ref=ref,
        staged=staged,
        model=model,
        raw_patch=raw_patch,
        exclude_generated=exclude_generated,
    )
