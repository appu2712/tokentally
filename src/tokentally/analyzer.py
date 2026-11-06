"""
Deep prompt context analyzer, component attribution engine, and cacheability auditor.
Breaks down monolithic prompts into structural components (system, user, history, tools, RAG)
and identifies cache-breaking patterns, bloat hotspots, and reasoning token costs.
"""

from dataclasses import dataclass, asdict
import json
import re
from typing import Any, Dict, List, Optional

from .counter import count_tokens_detailed
from .calculator import estimate_cost
from .models import get_model_pricing, normalize_model_name


# Patterns that break prompt caching when located near the start of a prompt
DYNAMIC_CACHE_BREAKERS = [
    (re.compile(r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}"), "ISO Timestamp"),
    (re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"), "UUID / Request ID"),
    (re.compile(r"\b(nonce|timestamp|req_id|trace_id|session_id)\s*[:=]\s*\S+", re.IGNORECASE), "Dynamic session identifier"),
    (re.compile(r"\b(current time is|today's date is)\b", re.IGNORECASE), "Volatile datetime preamble"),
]


@dataclass
class ContextComponent:
    name: str
    tokens: int
    pct_of_total: float
    cost_usd: float
    is_cacheable: bool
    description: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheabilityReport:
    static_prefix_tokens: int
    dynamic_tokens: int
    cache_eligible: bool  # True if static prefix exceeds provider caching threshold (~1,024 tokens)
    estimated_cache_hit_rate_pct: float
    cache_breaking_items: List[str]
    potential_cached_savings_usd: float
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReasoningTokenAnalysis:
    is_reasoning_model: bool
    estimated_reasoning_tokens_low: int
    estimated_reasoning_tokens_high: int
    estimated_cost_low_usd: float
    estimated_cost_high_usd: float
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PromptAnalysisResult:
    total_tokens: int
    token_method: str
    is_exact_tokenizer: bool
    model: str
    total_cost_usd: float
    components: List[ContextComponent]
    cacheability: CacheabilityReport
    reasoning_estimate: ReasoningTokenAnalysis
    bloat_warnings: List[str]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tokens": self.total_tokens,
            "token_method": self.token_method,
            "is_exact_tokenizer": self.is_exact_tokenizer,
            "model": self.model,
            "total_cost_usd": self.total_cost_usd,
            "components": [c.to_dict() for c in self.components],
            "cacheability": self.cacheability.to_dict(),
            "reasoning_estimate": self.reasoning_estimate.to_dict(),
            "bloat_warnings": self.bloat_warnings,
            "recommendations": self.recommendations,
        }


class PromptContextAnalyzer:
    """Analyzes and attributes prompt tokens to specific layers and evaluates caching potential."""

    def __init__(self):
        pass

    def _try_parse_chat_messages(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """Try parsing JSON formatted chat messages."""
        trimmed = text.strip()
        if (trimmed.startswith("[") and trimmed.endswith("]")) or (trimmed.startswith("{") and trimmed.endswith("}")):
            try:
                data = json.loads(trimmed)
                if isinstance(data, list) and all(isinstance(m, dict) and "role" in m for m in data):
                    return data
                if isinstance(data, dict) and "messages" in data and isinstance(data["messages"], list):
                    return data["messages"]
            except Exception:
                pass
        return None

    def analyze(self, prompt: str, model: str = "gpt-4o") -> PromptAnalysisResult:
        canonical_model = normalize_model_name(model)
        pricing = get_model_pricing(canonical_model)

        cnt_res = count_tokens_detailed(prompt, model=canonical_model)
        total_tokens = cnt_res.tokens
        method_name = cnt_res.method
        is_exact = cnt_res.is_exact

        base_cost = estimate_cost(total_tokens, model=canonical_model).total_cost_usd

        # 1. Component Segmentation
        components: List[ContextComponent] = []
        bloat_warnings: List[str] = []
        recommendations: List[str] = []

        chat_messages = self._try_parse_chat_messages(prompt)
        if chat_messages:
            # Chat messages structure
            comp_map = {
                "system_instructions": "",
                "developer_instructions": "",
                "conversation_history": "",
                "tool_definitions_or_calls": "",
                "tool_outputs": "",
                "user_request": "",
            }

            for idx, msg in enumerate(chat_messages):
                role = msg.get("role", "user").lower()
                content = str(msg.get("content", ""))
                if "tool_calls" in msg or role == "tool_calls":
                    comp_map["tool_definitions_or_calls"] += "\n" + json.dumps(msg.get("tool_calls", content))
                elif role in ("system", "developer"):
                    comp_map["system_instructions"] += "\n" + content
                elif role == "tool":
                    comp_map["tool_outputs"] += "\n" + content
                elif idx == len(chat_messages) - 1 and role == "user":
                    comp_map["user_request"] += "\n" + content
                else:
                    comp_map["conversation_history"] += f"\n[{role}]: {content}"

            for c_name, c_text in comp_map.items():
                if c_text.strip():
                    c_tok = count_tokens_detailed(c_text, model=canonical_model).tokens
                    c_pct = (c_tok / total_tokens * 100.0) if total_tokens > 0 else 0.0
                    c_cost = (c_tok / 1_000_000.0) * pricing.input_per_m
                    is_cache = c_name in ("system_instructions", "developer_instructions")
                    components.append(
                        ContextComponent(
                            name=c_name,
                            tokens=c_tok,
                            pct_of_total=round(c_pct, 2),
                            cost_usd=round(c_cost, 8),
                            is_cacheable=is_cache,
                            description=f"Chat layer: {c_name.replace('_', ' ').title()}",
                        )
                    )
        else:
            # Markdown / Text section heuristic segmentation
            section_patterns = [
                (re.compile(r"(?i)(^|\n)#{1,3}\s*(system|instructions|guidelines|rules|persona)(.*?)((?=\n#{1,3}\s)|\Z)", re.DOTALL), "system_instructions"),
                (re.compile(r"(?i)(^|\n)#{1,3}\s*(tools?|functions?|capabilities)(.*?)((?=\n#{1,3}\s)|\Z)", re.DOTALL), "tool_definitions"),
                (re.compile(r"(?i)(^|\n)#{1,3}\s*(context|documents?|knowledge|sources?|retrieval)(.*?)((?=\n#{1,3}\s)|\Z)", re.DOTALL), "rag_context"),
                (re.compile(r"(?i)(^|\n)#{1,3}\s*(history|conversation|previous|chat)(.*?)((?=\n#{1,3}\s)|\Z)", re.DOTALL), "conversation_history"),
                (re.compile(r"(?i)(^|\n)#{1,3}\s*(user|input|task|query|prompt)(.*?)((?=\n#{1,3}\s)|\Z)", re.DOTALL), "user_request"),
            ]

            remaining_text = prompt
            for pat, comp_name in section_patterns:
                m = pat.search(prompt)
                if m:
                    extracted = m.group(0)
                    c_tok = count_tokens_detailed(extracted, model=canonical_model).tokens
                    c_pct = (c_tok / total_tokens * 100.0) if total_tokens > 0 else 0.0
                    c_cost = (c_tok / 1_000_000.0) * pricing.input_per_m
                    components.append(
                        ContextComponent(
                            name=comp_name,
                            tokens=c_tok,
                            pct_of_total=round(c_pct, 2),
                            cost_usd=round(c_cost, 8),
                            is_cacheable=(comp_name == "system_instructions"),
                            description=f"Extracted section: {comp_name.replace('_', ' ').title()}",
                        )
                    )
                    remaining_text = remaining_text.replace(extracted, "")

            if not components:
                # Monolithic fallback
                components.append(
                    ContextComponent(
                        name="primary_prompt",
                        tokens=total_tokens,
                        pct_of_total=100.0,
                        cost_usd=round(base_cost, 8),
                        is_cacheable=False,
                        description="Unsegmented prompt body",
                    )
                )

        # 2. Cacheability and Prefix Inspection
        initial_chunk = prompt[:1500]  # Examine leading tokens for dynamic cache-breakers
        cache_breakers: List[str] = []
        for pat, label in DYNAMIC_CACHE_BREAKERS:
            if pat.search(initial_chunk):
                cache_breakers.append(label)

        # Estimate static prefix tokens (assumed to be system/developer instructions if placed at top)
        static_tokens = 0
        for comp in components:
            if comp.is_cacheable:
                static_tokens += comp.tokens

        # Most frontier providers require a minimum of 1,024 prefix tokens to activate prompt caching
        cache_eligible = (static_tokens >= 1024) and (len(cache_breakers) == 0)

        cached_rate = pricing.cached_input_per_m if pricing.cached_input_per_m is not None else pricing.input_per_m
        full_rate = pricing.input_per_m
        potential_savings = max(0.0, (static_tokens / 1_000_000.0) * (full_rate - cached_rate))

        if cache_breakers:
            cache_rec = f"Move dynamic elements ({', '.join(cache_breakers)}) from the prompt header to the user query at the bottom to restore prefix caching."
            bloat_warnings.append(f"Prompt caching invalidated: dynamic prefix detected ({', '.join(cache_breakers)}).")
        elif static_tokens < 1024:
            cache_rec = f"Static instructions ({static_tokens:,} tokens) are below the 1,024 token minimum required for provider prompt caching discounts."
        else:
            cache_rec = f"Prompt prefix is cleanly cached! Eligible for ~${potential_savings:.6f} discount per cached request."

        # Compute estimated cache hit rate
        cache_hit_rate = (static_tokens / total_tokens * 100.0) if (cache_eligible and total_tokens > 0) else 0.0

        cache_report = CacheabilityReport(
            static_prefix_tokens=static_tokens,
            dynamic_tokens=max(0, total_tokens - static_tokens),
            cache_eligible=cache_eligible,
            estimated_cache_hit_rate_pct=round(cache_hit_rate, 1),
            cache_breaking_items=cache_breakers,
            potential_cached_savings_usd=round(potential_savings, 8),
            recommendation=cache_rec,
        )

        # 3. Reasoning Token Modeling (OpenAI o1, o3-mini, DeepSeek R1)
        is_reasoning = canonical_model in ("o1", "o1-mini", "o3-mini", "deepseek-r1")
        if is_reasoning:
            # Reasoning tokens typically consume between 1x and 4x the input tokens for complex tasks
            low_r = int(total_tokens * 1.0)
            high_r = int(total_tokens * 3.5)
            r_cost_low = (low_r / 1_000_000.0) * pricing.output_per_m
            r_cost_high = (high_r / 1_000_000.0) * pricing.output_per_m
            reasoning_analysis = ReasoningTokenAnalysis(
                is_reasoning_model=True,
                estimated_reasoning_tokens_low=low_r,
                estimated_reasoning_tokens_high=high_r,
                estimated_cost_low_usd=round(r_cost_low, 6),
                estimated_cost_high_usd=round(r_cost_high, 6),
                explanation=f"{canonical_model} generates internal reasoning tokens (billed at output rate of ${pricing.output_per_m:.2f}/M) before emitting visible answers.",
            )
        else:
            reasoning_analysis = ReasoningTokenAnalysis(
                is_reasoning_model=False,
                estimated_reasoning_tokens_low=0,
                estimated_reasoning_tokens_high=0,
                estimated_cost_low_usd=0.0,
                estimated_cost_high_usd=0.0,
                explanation="Standard generation model (no internal hidden reasoning tokens).",
            )

        # 4. Bloat Diagnostics & Recommendations
        for comp in components:
            if comp.name == "conversation_history" and comp.pct_of_total > 50.0:
                bloat_warnings.append(
                    f"Conversation history consumes {comp.pct_of_total}% ({comp.tokens:,} tokens) of total context. Cumulative reprocessing will create O(n^2) cost amplification."
                )
                recommendations.append("Consider summarizing historical dialogue turns or maintaining structured state.")

            if comp.name == "tool_definitions" and comp.tokens > 3000:
                bloat_warnings.append(
                    f"Tool definitions consume {comp.tokens:,} tokens ({comp.pct_of_total}% of context). Models only invoke a fraction of exposed tools per step."
                )
                recommendations.append("Filter tool catalogs dynamically to expose only tools relevant to the current task.")

            if comp.name == "rag_context" and comp.tokens > 10000:
                bloat_warnings.append(
                    f"RAG context consumes {comp.tokens:,} tokens. High chunk volume increases 'Lost in the middle' quality degradation."
                )
                recommendations.append("Apply semantic reranking to reduce top-k chunks from retrieved context.")

        return PromptAnalysisResult(
            total_tokens=total_tokens,
            token_method=method_name,
            is_exact_tokenizer=is_exact,
            model=canonical_model,
            total_cost_usd=round(base_cost, 8),
            components=components,
            cacheability=cache_report,
            reasoning_estimate=reasoning_analysis,
            bloat_warnings=bloat_warnings,
            recommendations=recommendations,
        )


_DEFAULT_ANALYZER = PromptContextAnalyzer()


def analyze_prompt_context(prompt: str, model: str = "gpt-4o") -> PromptAnalysisResult:
    """Convenience helper to analyze prompt components and cacheability."""
    return _DEFAULT_ANALYZER.analyze(prompt, model=model)
