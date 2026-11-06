"""
Git diff token analyzer and code review cost profiler.
"""

from dataclasses import dataclass, asdict
import os
import subprocess
from typing import Any, Dict, List, Optional

from .counter import count_tokens
from .calculator import estimate_cost


@dataclass
class FileDiffStat:
    path: str
    tokens: int
    added_lines: int
    deleted_lines: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GitDiffResult:
    target_ref: str
    total_tokens: int
    files_changed: int
    estimated_review_cost_usd: float
    model: str
    file_breakdown: List[FileDiffStat]
    raw_diff: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target_ref": self.target_ref,
            "total_tokens": self.total_tokens,
            "files_changed": self.files_changed,
            "estimated_review_cost_usd": self.estimated_review_cost_usd,
            "model": self.model,
            "file_breakdown": [f.to_dict() for f in self.file_breakdown],
        }


class GitDiffProfiler:
    """Calculates token weight and review cost of git commits, staged changes, and branch PRs."""

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

        total_tokens = count_tokens(diff_text, model=model)
        # Cost estimate assuming 500 completion tokens for an AI code review summary
        cost_eval = estimate_cost(total_tokens, model=model, completion_tokens=500)

        # Parse individual file changes from git diff output
        file_stats: List[FileDiffStat] = []
        chunks = diff_text.split("diff --git ")

        for chunk in chunks:
            if not chunk.strip():
                continue
            lines = chunk.splitlines()
            first_line = lines[0] if lines else ""
            # e.g. "a/src/main.py b/src/main.py"
            parts = first_line.split(" ")
            filepath = parts[-1].lstrip("b/") if parts else "unknown"

            added = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
            deleted = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
            chunk_tokens = count_tokens(chunk, model=model)

            file_stats.append(
                FileDiffStat(
                    path=filepath,
                    tokens=chunk_tokens,
                    added_lines=added,
                    deleted_lines=deleted,
                )
            )

        return GitDiffResult(
            target_ref=ref_label,
            total_tokens=total_tokens,
            files_changed=len(file_stats),
            estimated_review_cost_usd=cost_eval.total_cost_usd,
            model=model,
            file_breakdown=file_stats,
            raw_diff=diff_text,
        )


_DEFAULT_GIT_PROFILER = GitDiffProfiler()


def profile_git_diff(
    ref: Optional[str] = None,
    staged: bool = False,
    model: str = "gpt-4o",
    raw_patch: Optional[str] = None,
) -> GitDiffResult:
    """Convenience helper to profile git diff."""
    return _DEFAULT_GIT_PROFILER.profile_diff(
        ref=ref, staged=staged, model=model, raw_patch=raw_patch
    )
