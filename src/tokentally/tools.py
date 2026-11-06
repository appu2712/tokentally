"""
Tool schema analyzer, agent loop detector, and multi-turn cumulative history simulator.
"""

from dataclasses import dataclass, asdict
import json
import os
from typing import Any, Dict, List, Optional, Union

from .counter import count_tokens_detailed
from .calculator import estimate_cost


@dataclass
class ToolSchemaStat:
    name: str
    tokens: int
    field_count: int
    max_depth: int
    description_tokens: int
    description_pct: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolCatalogReport:
    total_tools: int
    total_tokens: int
    cost_per_request_usd: float
    model: str
    tools: List[ToolSchemaStat]
    recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tools": self.total_tools,
            "total_tokens": self.total_tokens,
            "cost_per_request_usd": self.cost_per_request_usd,
            "model": self.model,
            "tools": [t.to_dict() for t in self.tools],
            "recommendations": self.recommendations,
        }


@dataclass
class HistorySimulationResult:
    num_turns: int
    avg_tokens_per_turn: int
    final_turn_context_tokens: int
    cumulative_processed_tokens: int
    cumulative_overhead_multiplier: float
    single_turn_cost_usd: float
    cumulative_total_cost_usd: float
    model: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentLoopReport:
    total_steps: int
    duplicate_calls: int
    loop_detected: bool
    progress_per_token_score: float  # 0.0 to 1.0
    detected_cycles: List[str]
    recommendations: List[str]

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


class ToolWorkloadEngine:
    """Analyzes function calling schemas, simulates cumulative context, and audits agent loops."""

    def __init__(self):
        pass

    def _calc_schema_depth(self, obj: Any, depth: int = 1) -> int:
        if not isinstance(obj, dict):
            return depth
        max_d = depth
        for v in obj.values():
            if isinstance(v, dict):
                max_d = max(max_d, self._calc_schema_depth(v, depth + 1))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                max_d = max(max_d, self._calc_schema_depth(v[0], depth + 1))
        return max_d

    def _count_fields(self, schema: Dict[str, Any]) -> int:
        count = 0
        props = schema.get("properties", {})
        count += len(props)
        for val in props.values():
            if isinstance(val, dict) and "properties" in val:
                count += self._count_fields(val)
        return count

    def analyze_tool_schemas(
        self,
        tools_input: Union[str, List[Dict[str, Any]], Dict[str, Any]],
        model: str = "gpt-4o",
    ) -> ToolCatalogReport:
        if isinstance(tools_input, str):
            if os.path.isfile(tools_input):
                with open(tools_input, "r", encoding="utf-8", errors="replace") as f:
                    tools_input = f.read()
            elif _looks_like_file_path(tools_input) and not os.path.exists(tools_input):
                raise FileNotFoundError(f"Tool schema file not found: '{tools_input}'")
            try:
                tools_data = json.loads(tools_input)
            except Exception as e:
                raise ValueError(f"Invalid JSON for tool schemas: {e}")
        else:
            tools_data = tools_input

        # Handle various tool wrapping formats (OpenAI tools array, LangChain, or raw dict)
        if isinstance(tools_data, dict):
            if "tools" in tools_data and isinstance(tools_data["tools"], list):
                tool_list = tools_data["tools"]
            elif "functions" in tools_data and isinstance(tools_data["functions"], list):
                tool_list = tools_data["functions"]
            else:
                tool_list = [tools_data]
        else:
            tool_list = tools_data

        stats: List[ToolSchemaStat] = []
        total_tokens = 0
        recommendations: List[str] = []

        for item in tool_list:
            if not isinstance(item, dict):
                continue

            # OpenAI format: {"type": "function", "function": {"name": ..., "parameters": ...}}
            fn = item.get("function", item)
            name = fn.get("name", "unnamed_tool")
            desc = fn.get("description", "")
            params = fn.get("parameters", {})

            item_json = json.dumps(item, indent=2)
            t_tok = count_tokens_detailed(item_json, model=model).tokens
            d_tok = count_tokens_detailed(desc, model=model).tokens

            field_cnt = self._count_fields(params) if isinstance(params, dict) else 0
            depth = self._calc_schema_depth(params) if isinstance(params, dict) else 1

            total_tokens += t_tok
            desc_pct = (d_tok / t_tok * 100.0) if t_tok > 0 else 0.0

            stats.append(
                ToolSchemaStat(
                    name=name,
                    tokens=t_tok,
                    field_count=field_cnt,
                    max_depth=depth,
                    description_tokens=d_tok,
                    description_pct=round(desc_pct, 1),
                )
            )

        cost_res = estimate_cost(total_tokens, model=model)

        if len(stats) > 10:
            recommendations.append(
                f"Tool catalog contains {len(stats)} tools ({total_tokens:,} tokens). "
                "Consider dynamic tool retrieval or sub-agent delegation to only expose tools relevant to the active subtask."
            )

        oversized = [s for s in stats if s.tokens > 1000]
        if oversized:
            recommendations.append(
                f"{len(oversized)} tool schemas exceed 1,000 tokens each ({', '.join(s.name for s in oversized)}). "
                "Prune rarely used optional parameters and collapse nested objects."
            )

        return ToolCatalogReport(
            total_tools=len(stats),
            total_tokens=total_tokens,
            cost_per_request_usd=cost_res.total_cost_usd,
            model=model,
            tools=stats,
            recommendations=recommendations,
        )

    def simulate_history_growth(
        self,
        num_turns: int = 10,
        tokens_per_turn: int = 500,
        model: str = "gpt-4o",
    ) -> HistorySimulationResult:
        """
        Simulate cumulative token reprocessing across n turns.
        Formula: cumulative = k * n * (n + 1) / 2
        """
        n = max(1, num_turns)
        k = max(1, tokens_per_turn)

        final_context = n * k
        cumulative = int(k * (n * (n + 1) / 2.0))
        multiplier = cumulative / final_context if final_context > 0 else 1.0

        single_cost = estimate_cost(final_context, model=model).total_cost_usd
        cum_cost = estimate_cost(cumulative, model=model).total_cost_usd

        rec = (
            f"Over {n} turns, naive history re-sending forces the model to process {cumulative:,} cumulative tokens "
            f"({multiplier:.1f}x the final {final_context:,} token state). "
            f"Compressing historical turns into a state object saves ${cum_cost - single_cost:.4f} per session."
        )

        return HistorySimulationResult(
            num_turns=n,
            avg_tokens_per_turn=k,
            final_turn_context_tokens=final_context,
            cumulative_processed_tokens=cumulative,
            cumulative_overhead_multiplier=round(multiplier, 2),
            single_turn_cost_usd=round(single_cost, 6),
            cumulative_total_cost_usd=round(cum_cost, 6),
            model=model,
            recommendation=rec,
        )

    def audit_agent_trace(
        self,
        steps: List[Dict[str, Any]],
        tokens_per_step: int = 2000,
    ) -> AgentLoopReport:
        """
        Detect loops, cyclic tool execution, and low progress-per-token in agent trajectories.
        """
        seen_calls: Dict[str, int] = {}
        duplicates = 0
        cycles: List[str] = []

        for step in steps:
            tool_name = step.get("tool") or step.get("name") or "unknown"
            args_str = json.dumps(step.get("args") or step.get("arguments") or {}, sort_keys=True)
            sig = f"{tool_name}:{args_str}"

            if sig in seen_calls:
                duplicates += 1
                seen_calls[sig] += 1
                if seen_calls[sig] == 2:
                    cycles.append(f"Repeated execution of '{tool_name}' with identical arguments.")
            else:
                seen_calls[sig] = 1

        total_steps = len(steps)
        loop_detected = duplicates >= 2

        # Progress per token heuristic: decreases rapidly with duplicates
        progress_score = max(0.0, 1.0 - (duplicates / max(1, total_steps)))

        recs = []
        if loop_detected:
            recs.append("Agent loop detected: identical tool calls executed multiple times with no state change.")
            recs.append("Enforce maximum identical call limits (max 2) before forcing fallback to user clarification.")

        return AgentLoopReport(
            total_steps=total_steps,
            duplicate_calls=duplicates,
            loop_detected=loop_detected,
            progress_per_token_score=round(progress_score, 2),
            detected_cycles=cycles,
            recommendations=recs,
        )


_DEFAULT_TOOL_ENGINE = ToolWorkloadEngine()


def analyze_tool_schemas(
    tools_input: Union[str, List[Dict[str, Any]], Dict[str, Any]],
    model: str = "gpt-4o",
) -> ToolCatalogReport:
    """Convenience helper to audit tool schemas."""
    return _DEFAULT_TOOL_ENGINE.analyze_tool_schemas(tools_input, model=model)


def simulate_history_growth(
    num_turns: int = 10,
    tokens_per_turn: int = 500,
    model: str = "gpt-4o",
) -> HistorySimulationResult:
    """Convenience helper to simulate cumulative O(n^2) history."""
    return _DEFAULT_TOOL_ENGINE.simulate_history_growth(num_turns, tokens_per_turn, model=model)
