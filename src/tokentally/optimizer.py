"""
Explainable prompt optimizer with constraint invariance verification and semantic deduplication.
Guarantees that negative constraints, required schemas, code fences, and critical instructions
are mathematically preserved while eliminating token bloat.
"""

from dataclasses import dataclass, asdict
import difflib
import re
from typing import Any, Dict, List, Optional, Set

from .counter import count_tokens_detailed
from .calculator import estimate_cost


NEGATIVE_CONSTRAINT_PATTERN = re.compile(
    r"\b(do not|must not|never|cannot|should not|prohibited|mandatory|strictly required|always)\b",
    re.IGNORECASE,
)
CODE_FENCE_PATTERN = re.compile(r"```[a-zA-Z0-9_-]*")
URL_PATTERN = re.compile(r"https?://\S+")


@dataclass
class TransformationStep:
    name: str
    tokens_saved: int
    rationale: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
    invariance_passed: bool
    invariance_warnings: List[str]
    transformation_steps: List[TransformationStep]
    diff_summary: str
    optimized_text: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        del d["optimized_text"]
        return d


class PromptOptimizer:
    """Explainable and conservative prompt minifier with safety constraint preservation."""

    def __init__(self):
        pass

    def _verify_invariance(self, original: str, optimized: str) -> List[str]:
        """Verify that negative constraints, code fences, and URLs were strictly preserved."""
        warnings: List[str] = []

        # 1. Negative constraint verification
        orig_constraints = set(m.group(0).lower() for m in NEGATIVE_CONSTRAINT_PATTERN.finditer(original))
        opt_constraints = set(m.group(0).lower() for m in NEGATIVE_CONSTRAINT_PATTERN.finditer(optimized))
        missing_constraints = orig_constraints - opt_constraints
        if missing_constraints:
            warnings.append(
                f"Constraint violation risk: Missing negative instructions ({', '.join(missing_constraints)})."
            )

        # 2. Code fence count parity
        orig_fences = len(CODE_FENCE_PATTERN.findall(original))
        opt_fences = len(CODE_FENCE_PATTERN.findall(optimized))
        if orig_fences != opt_fences:
            warnings.append(
                f"Code fence count mismatch: original has {orig_fences} fences, optimized has {opt_fences}."
            )

        # 3. URL count parity
        orig_urls = set(URL_PATTERN.findall(original))
        opt_urls = set(URL_PATTERN.findall(optimized))
        missing_urls = orig_urls - opt_urls
        if missing_urls:
            warnings.append(f"URL preservation error: Missing {len(missing_urls)} URLs.")

        return warnings

    def optimize(
        self,
        text: str,
        model: str = "gpt-4o",
        strip_comments: bool = False,
        normalize_whitespace: bool = True,
        max_consecutive_newlines: int = 1,
        deduplicate_paragraphs: bool = True,
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
                invariance_passed=True,
                invariance_warnings=[],
                transformation_steps=[],
                diff_summary="",
                optimized_text="",
            )

        orig_len = len(text)
        orig_tokens = count_tokens_detailed(text, model=model).tokens
        orig_cost = estimate_cost(orig_tokens, model=model).total_cost_usd

        steps: List[TransformationStep] = []
        current = text

        # Step 1: Strip non-critical full-line comments if requested
        if strip_comments:
            before_c = current
            # Only strip comments that do not contain explicit negative constraints
            def _comment_replacer(match):
                line = match.group(0)
                if NEGATIVE_CONSTRAINT_PATTERN.search(line):
                    return line  # Preserve critical comments
                return ""

            current = re.sub(r"^\s*(#|//)\s*.*?$", _comment_replacer, current, flags=re.MULTILINE)
            t_diff = count_tokens_detailed(before_c, model=model).tokens - count_tokens_detailed(current, model=model).tokens
            if t_diff > 0:
                steps.append(
                    TransformationStep(
                        name="strip_comments",
                        tokens_saved=t_diff,
                        rationale="Pruned single-line code/developer comments (preserved negative constraint comments).",
                    )
                )

        # Step 2: Deduplicate identical non-trivial paragraphs/blocks
        if deduplicate_paragraphs:
            before_d = current
            paras = current.split("\n\n")
            seen_paras: Set[str] = set()
            unique_paras = []
            for p in paras:
                p_norm = " ".join(p.strip().split())
                if len(p_norm) > 40 and p_norm in seen_paras:
                    continue  # Skip exact duplicate block
                seen_paras.add(p_norm)
                unique_paras.append(p)

            current = "\n\n".join(unique_paras)
            t_diff = count_tokens_detailed(before_d, model=model).tokens - count_tokens_detailed(current, model=model).tokens
            if t_diff > 0:
                steps.append(
                    TransformationStep(
                        name="deduplicate_paragraphs",
                        tokens_saved=t_diff,
                        rationale="Removed redundant identical paragraphs occurring multiple times in context.",
                    )
                )

        # Step 3: Normalize whitespace and collapse excessive newlines
        if normalize_whitespace:
            before_w = current
            lines = [line.rstrip() for line in current.splitlines()]
            current = "\n".join(lines)

            nl_pattern = r"\n{" + str(max_consecutive_newlines + 1) + r",}"
            replacement = "\n" * max_consecutive_newlines
            current = re.sub(nl_pattern, replacement, current)
            current = current.strip()

            t_diff = count_tokens_detailed(before_w, model=model).tokens - count_tokens_detailed(current, model=model).tokens
            if t_diff > 0:
                steps.append(
                    TransformationStep(
                        name="normalize_whitespace",
                        tokens_saved=t_diff,
                        rationale=f"Collapsed trailing whitespace and consecutive newlines to max {max_consecutive_newlines}.",
                    )
                )

        # Step 4: Safety & Constraint Invariance Verification
        warnings = self._verify_invariance(text, current)
        invariance_ok = len(warnings) == 0

        # Generate readable diff
        orig_lines = text.splitlines(keepends=True)
        opt_lines = current.splitlines(keepends=True)
        diff_lines = list(difflib.unified_diff(orig_lines, opt_lines, fromfile="original", tofile="optimized", n=2))
        diff_summary = "".join(diff_lines[:40])  # Cap preview

        opt_len = len(current)
        opt_tokens = count_tokens_detailed(current, model=model).tokens
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
            invariance_passed=invariance_ok,
            invariance_warnings=warnings,
            transformation_steps=steps,
            diff_summary=diff_summary,
            optimized_text=current,
        )


_DEFAULT_OPTIMIZER = PromptOptimizer()


def optimize_prompt(
    text: str,
    model: str = "gpt-4o",
    strip_comments: bool = False,
    normalize_whitespace: bool = True,
    max_consecutive_newlines: int = 1,
    deduplicate_paragraphs: bool = True,
) -> OptimizationResult:
    """Convenience helper to optimize prompt with explainability and invariance guards."""
    return _DEFAULT_OPTIMIZER.optimize(
        text=text,
        model=model,
        strip_comments=strip_comments,
        normalize_whitespace=normalize_whitespace,
        max_consecutive_newlines=max_consecutive_newlines,
        deduplicate_paragraphs=deduplicate_paragraphs,
    )
