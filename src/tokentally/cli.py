"""
Command-line interface for tokentally.
"""

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .counter import count_tokens, count_tokens_detailed
from .calculator import estimate_cost, compare_models
from .packer import pack_repository
from .guard import check_budget
from .optimizer import optimize_prompt
from .git import profile_git_diff
from .reporter import generate_report
from .mcp import MCPServer
from .server import start_server
from .hooks import scaffold_github_workflow, install_git_precommit_hook
from .analyzer import analyze_prompt_context
from .regression import compare_prompt_regression
from .tools import analyze_tool_schemas, simulate_history_growth
from .config import load_config
from .models import MODEL_REGISTRY, list_supported_models

# Ensure stdout encoding is safe across all platforms
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _supports_color() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


USE_COLOR = _supports_color()

BOLD = "\033[1m" if USE_COLOR else ""
GREEN = "\033[32m" if USE_COLOR else ""
CYAN = "\033[36m" if USE_COLOR else ""
YELLOW = "\033[33m" if USE_COLOR else ""
RED = "\033[31m" if USE_COLOR else ""
MAGENTA = "\033[35m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""

CHECKMARK = "[PASS]"
CROSSMARK = "[FAIL]"


def _render_bar(pct: float, width: int = 14) -> str:
    """Render a terminal ASCII distribution bar."""
    filled = int(round(width * (pct / 100.0)))
    filled = max(0, min(width, filled))
    return f"[{'#' * filled}{'-' * (width - filled)}]"


def _read_input_target(target: Optional[str]) -> str:
    """Read content from target argument, stdin pipe, or file."""
    if target and target != "-":
        if os.path.isfile(target):
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return target

    if target == "-":
        return sys.stdin.read()

    return ""


def handle_count(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No input text, file, or piped content provided.\n")
        return 1

    res = count_tokens_detailed(content, model=args.model)

    if args.json:
        print(json.dumps({
            "target": args.target or "stdin",
            "model": args.model,
            "tokens": res.tokens,
            "method": res.method,
            "encoding": res.encoding,
            "is_exact": res.is_exact,
        }, indent=2))
    else:
        method_badge = f"{GREEN}[exact BPE: {res.encoding}]{RESET}" if res.is_exact else f"{YELLOW}[calibrated heuristic]{RESET}"
        print(f"{BOLD}Tokens:{RESET} {CYAN}{res.tokens:,}{RESET} {DIM}(model: {args.model}){RESET} {method_badge}")
    return 0


def handle_cost(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No input text, file, or piped content provided.\n")
        return 1

    res = estimate_cost(
        prompt=content,
        model=args.model,
        completion_tokens=args.completion_tokens,
        cached_tokens=args.cached_tokens,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== TokenTally Cost Estimation ==={RESET}")
    print(f"  {BOLD}Model:{RESET}            {res.model} ({res.provider})")
    print(f"  {BOLD}Input Tokens:{RESET}     {res.input_tokens:,}")
    if res.cached_tokens > 0:
        print(f"  {BOLD}Cached Tokens:{RESET}    {res.cached_tokens:,} {DIM}(cached rate applied){RESET}")
    print(f"  {BOLD}Output Tokens:{RESET}    {res.output_tokens:,}")
    print(f"  {BOLD}Total Tokens:{RESET}     {res.total_tokens:,}")
    print(f"  {DIM}--------------------------------{RESET}")
    print(f"  {BOLD}Input Cost:{RESET}       ${res.input_cost_usd:.6f}")
    if res.cached_tokens > 0:
        print(f"  {BOLD}Cached Cost:{RESET}      ${res.cached_cost_usd:.6f}")
    print(f"  {BOLD}Output Cost:{RESET}      ${res.output_cost_usd:.6f}")
    print(f"  {BOLD}{GREEN}Total Cost:{RESET}       {BOLD}{GREEN}${res.total_cost_usd:.6f}{RESET}\n")
    return 0


def handle_compare(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No input text, file, or piped content provided.\n")
        return 1

    models = args.models.split(",") if args.models else None
    rows = compare_models(
        prompt=content,
        models=models,
        completion_ratio=args.completion_ratio,
    )

    if args.json:
        print(json.dumps([r.to_dict() for r in rows], indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== Multi-Model Cost Comparison ==={RESET}")
    header = f"{'MODEL':<22} {'PROVIDER':<14} {'IN TOK':<9} {'OUT TOK':<9} {'TOTAL COST':<14} {'RATIO'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * len(header))

    for r in rows:
        ratio_str = f"{r.relative_ratio:.2f}x"
        color = GREEN if r.relative_ratio <= 1.0 else YELLOW if r.relative_ratio < 5.0 else RED
        print(
            f"{r.model:<22} {r.provider:<14} {r.input_tokens:<9,d} {r.output_tokens:<9,d} "
            f"{color}${r.total_cost_usd:<13.6f}{RESET} {DIM}{ratio_str}{RESET}"
        )
    print()
    return 0


def handle_analyze(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No input text provided.\n")
        return 1

    res = analyze_prompt_context(content, model=args.model)

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    tokenizer_badge = f"{GREEN}[exact BPE]{RESET}" if res.is_exact_tokenizer else f"{YELLOW}[calibrated heuristic]{RESET}"
    print(f"\n{BOLD}{CYAN}=== TokenTally Context & Bloat Audit ==={RESET}")
    print(f"  {BOLD}Total Tokens:{RESET}       {CYAN}{res.total_tokens:,}{RESET} {tokenizer_badge}")
    print(f"  {BOLD}Model Evaluated:{RESET}    {res.model} (${res.total_cost_usd:.6f}/call)")

    print(f"\n{BOLD}Context Components Attribution:{RESET}")
    header = f"  {'LAYER':<24} {'TOKENS':<9} {'DISTRIBUTION':<18} {'PERCENT':<9} {'EST. COST':<12} {'CACHEABLE'}"
    print(f"{BOLD}{header}{RESET}")
    print("  " + "-" * 88)
    for c in res.components:
        cache_str = f"{GREEN}Yes{RESET}" if c.is_cacheable else f"{DIM}No{RESET}"
        bar = _render_bar(c.pct_of_total)
        print(f"  {c.name:<24} {c.tokens:<9,d} {CYAN}{bar:<18}{RESET} {c.pct_of_total:<9.1f}% ${c.cost_usd:<11.6f} {cache_str}")

    print(f"\n{BOLD}Prompt Caching Analysis:{RESET}")
    print(f"  {BOLD}Static Prefix Tokens:{RESET}   {res.cacheability.static_prefix_tokens:,}")
    print(f"  {BOLD}Dynamic Tokens:{RESET}        {res.cacheability.dynamic_tokens:,}")
    print(f"  {BOLD}Cache Status:{RESET}          {GREEN}Eligible{RESET}" if res.cacheability.cache_eligible else f"  {BOLD}Cache Status:{RESET}          {YELLOW}Not Eligible / Broken{RESET}")
    print(f"  {BOLD}Estimated Hit Rate:{RESET}    {BOLD}{GREEN}{res.cacheability.estimated_cache_hit_rate_pct}%{RESET}")
    print(f"  {BOLD}Recommendation:{RESET}        {res.cacheability.recommendation}")

    if res.reasoning_estimate.is_reasoning_model:
        print(f"\n{BOLD}Reasoning Token Projections (o1 / o3-mini / R1):{RESET}")
        print(f"  {BOLD}Estimated Hidden Tokens:{RESET} {res.reasoning_estimate.estimated_reasoning_tokens_low:,} - {res.reasoning_estimate.estimated_reasoning_tokens_high:,}")
        print(f"  {BOLD}Estimated Total Spend:{RESET}   ${res.reasoning_estimate.estimated_cost_low_usd:.4f} - ${res.reasoning_estimate.estimated_cost_high_usd:.4f}")
        print(f"  {DIM}{res.reasoning_estimate.explanation}{RESET}")

    if res.bloat_warnings:
        print(f"\n{BOLD}{YELLOW}Bloat Warnings & Diagnostics:{RESET}")
        for w in res.bloat_warnings:
            print(f"  {YELLOW}• {w}{RESET}")

    if res.recommendations:
        print(f"\n{BOLD}{GREEN}Optimization Recommendations:{RESET}")
        for r in res.recommendations:
            print(f"  {GREEN}✓ {r}{RESET}")
    print()
    return 0


def handle_diff(args: argparse.Namespace) -> int:
    stdin_content = None
    if args.ref == "-":
        stdin_content = sys.stdin.read()
        args.ref = None

    exclude_gen = args.exclude_generated or getattr(args, "ignore_generated", False)

    try:
        diff_res = profile_git_diff(
            ref=args.ref,
            staged=args.staged,
            model=args.model,
            raw_patch=stdin_content,
            exclude_generated=exclude_gen,
        )
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} {e}\n")
        return 1

    if args.json:
        print(json.dumps(diff_res.to_dict(), indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== Git Diff AI Review Cost Profiler ==={RESET}")
    print(f"  {BOLD}Target Ref:{RESET}           {diff_res.target_ref}")
    print(f"  {BOLD}Files Modified:{RESET}       {diff_res.files_changed}")
    print(f"  {BOLD}Effective Review Tokens:{RESET} {CYAN}{diff_res.total_tokens:,}{RESET} {DIM}(model: {diff_res.model}){RESET}")
    print(f"  {BOLD}Human Logic Tokens:{RESET}   {diff_res.human_code_tokens:,}")
    print(f"  {BOLD}Generated/Lock Tokens:{RESET}{YELLOW}{diff_res.generated_tokens:,}{RESET}")
    print(f"  {BOLD}Review Value Density:{RESET} {BOLD}{GREEN}{diff_res.review_value_density * 100:.1f}%{RESET}")
    print(f"  {BOLD}Estimated Review Cost:{RESET}{GREEN}${diff_res.estimated_review_cost_usd:.6f}{RESET}\n")

    if diff_res.file_breakdown:
        print(f"{BOLD}{'FILE':<38} {'TOKENS':<10} {'CATEGORY':<14} {'CHANGES'}{RESET}")
        print("-" * 72)
        for f in diff_res.file_breakdown:
            cat_color = YELLOW if f.is_generated else CYAN
            print(f"{f.path:<38} {f.tokens:<10,d} {cat_color}{f.category:<14}{RESET} {GREEN}+{f.added_lines}{RESET}/{RED}-{f.deleted_lines}{RESET}")

    if diff_res.recommendations:
        print()
        for r in diff_res.recommendations:
            print(f"  {YELLOW}• {r}{RESET}")
    print()
    return 0


def handle_regression(args: argparse.Namespace) -> int:
    try:
        reg_res = compare_prompt_regression(
            baseline=args.baseline,
            candidate=args.candidate,
            model=args.model,
            max_regression_pct=args.max_regression_pct,
        )
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} {e}\n")
        return 1

    if args.json:
        print(json.dumps(reg_res.to_dict(), indent=2))
        return 1 if reg_res.is_violation else 0

    print(f"\n{BOLD}{CYAN}=== Prompt Token Regression Audit ==={RESET}")
    print(f"  {BOLD}Baseline Tokens:{RESET}    {reg_res.baseline_tokens:,} (${reg_res.baseline_cost_usd:.6f})")
    print(f"  {BOLD}Candidate Tokens:{RESET}   {reg_res.candidate_tokens:,} (${reg_res.candidate_cost_usd:.6f})")

    delta_color = RED if reg_res.delta_tokens > 0 else GREEN
    sign = "+" if reg_res.delta_tokens > 0 else ""
    print(f"  {BOLD}Token Delta:{RESET}        {delta_color}{sign}{reg_res.delta_tokens:,} tokens ({sign}{reg_res.percent_change}%){RESET}")
    print(f"  {BOLD}Monthly Cost Impact:{RESET}{delta_color}{sign}${reg_res.projected_monthly_impact_10k_usd:,.2f} / 10k calls{RESET}")

    if reg_res.is_violation:
        print(f"\n{BOLD}{RED}{CROSSMARK} {reg_res.message}{RESET}\n")
        return 1
    else:
        print(f"\n{BOLD}{GREEN}{CHECKMARK} {reg_res.message}{RESET}\n")
        return 0


def handle_tools(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No tool JSON file or content provided.\n")
        return 1

    try:
        report = analyze_tool_schemas(content, model=args.model)
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} {e}\n")
        return 1

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== Tool Schema Context & Bloat Audit ==={RESET}")
    print(f"  {BOLD}Total Tools Exposed:{RESET}  {report.total_tools}")
    print(f"  {BOLD}Total Schema Tokens:{RESET}  {CYAN}{report.total_tokens:,}{RESET}")
    print(f"  {BOLD}Fixed Overhead/Call:{RESET}  ${report.cost_per_request_usd:.6f}\n")

    print(f"{BOLD}{'TOOL NAME':<30} {'TOKENS':<10} {'FIELDS':<8} {'DEPTH':<8} {'DESC %'}{RESET}")
    print("-" * 65)
    for t in report.tools:
        print(f"{t.name:<30} {t.tokens:<10,d} {t.field_count:<8} {t.max_depth:<8} {t.description_pct:>5.1f}%")

    if report.recommendations:
        print(f"\n{BOLD}{YELLOW}Tool Bloat Warnings:{RESET}")
        for r in report.recommendations:
            print(f"  {YELLOW}• {r}{RESET}")
    print()
    return 0


def handle_history(args: argparse.Namespace) -> int:
    res = simulate_history_growth(
        num_turns=args.turns,
        tokens_per_turn=args.tokens_per_turn,
        model=args.model,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== Multi-Turn History O(n^2) Cumulative Growth Simulation ==={RESET}")
    print(f"  {BOLD}Dialogue Turns:{RESET}            {res.num_turns}")
    print(f"  {BOLD}Tokens added/turn:{RESET}         {res.avg_tokens_per_turn:,}")
    print(f"  {BOLD}Final Single-Turn Context:{RESET} {res.final_turn_context_tokens:,} tokens (${res.single_turn_cost_usd:.6f})")
    print(f"  {BOLD}Cumulative Processed:{RESET}     {BOLD}{RED}{res.cumulative_processed_tokens:,} tokens{RESET} (${res.cumulative_total_cost_usd:.6f})")
    print(f"  {BOLD}Reprocessing Multiplier:{RESET}  {YELLOW}{res.cumulative_overhead_multiplier}x overhead{RESET}\n")
    print(f"  {GREEN}Recommendation:{RESET} {res.recommendation}\n")
    return 0


def handle_trace(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No agent trajectory JSON file provided.\n")
        return 1

    try:
        data = json.loads(content)
        steps = data if isinstance(data, list) else data.get("steps", [])
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} Invalid JSON trajectory: {e}\n")
        return 1

    from .tools import _DEFAULT_TOOL_ENGINE
    report = _DEFAULT_TOOL_ENGINE.audit_agent_trace(steps)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    status_str = f"{RED}[Loop Detected]{RESET}" if report.loop_detected else f"{GREEN}[No Loops]{RESET}"
    print(f"\n{BOLD}{CYAN}=== Agent Trajectory & Loop Audit ==={RESET}")
    print(f"  {BOLD}Total Trajectory Steps:{RESET} {report.total_steps}")
    print(f"  {BOLD}Duplicate Calls:{RESET}        {report.duplicate_calls} {status_str}")
    print(f"  {BOLD}Progress/Token Score:{RESET}   {CYAN}{report.progress_per_token_score:.2f}{RESET}")

    if report.detected_cycles:
        print(f"\n{BOLD}{RED}Detected Repetitive Cycles:{RESET}")
        for c in report.detected_cycles:
            print(f"  {RED}• {c}{RESET}")

    if report.recommendations:
        print(f"\n{BOLD}{YELLOW}Mitigation Recommendations:{RESET}")
        for r in report.recommendations:
            print(f"  {YELLOW}• {r}{RESET}")
    print()
    return 0


def handle_optimize(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No input text provided.\n")
        return 1

    opt_res = optimize_prompt(
        text=content,
        model=args.model,
        strip_comments=args.strip_comments,
    )

    if args.json:
        print(json.dumps(opt_res.to_dict(), indent=2))
        return 0

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(opt_res.optimized_text)

    invariance_badge = f"{GREEN}[Invariance: 100% Passed]{RESET}" if opt_res.invariance_passed else f"{RED}[Constraint Warning]{RESET}"
    print(f"\n{BOLD}{GREEN}{CHECKMARK} Prompt Optimization Complete!{RESET} {invariance_badge}")
    print(f"  {BOLD}Original Tokens:{RESET}   {opt_res.original_tokens:,} (${opt_res.original_cost_usd:.6f})")
    print(f"  {BOLD}Optimized Tokens:{RESET}  {CYAN}{opt_res.optimized_tokens:,}{RESET} (${opt_res.optimized_cost_usd:.6f})")
    print(f"  {BOLD}Tokens Saved:{RESET}      {BOLD}{GREEN}{opt_res.saved_tokens:,} ({opt_res.percent_reduction}% reduction){RESET}")
    print(f"  {BOLD}Per 10k Invocations:{RESET} Saves ${opt_res.saved_cost_usd * 10000:,.2f}")

    if opt_res.transformation_steps:
        print(f"\n{BOLD}Applied Transformations & Rationale:{RESET}")
        for s in opt_res.transformation_steps:
            print(f"  {GREEN}• {s.name:<25}{RESET} Saved {s.tokens_saved} tokens ({DIM}{s.rationale}{RESET})")

    if opt_res.invariance_warnings:
        print(f"\n{BOLD}{RED}Constraint Warnings:{RESET}")
        for w in opt_res.invariance_warnings:
            print(f"  {RED}! {w}{RESET}")

    if args.output:
        print(f"\n  {BOLD}Saved To:{RESET} {CYAN}{args.output}{RESET}")
    print()
    return 0


def handle_pack(args: argparse.Namespace) -> int:
    try:
        pack_res = pack_repository(
            directory=args.directory,
            output_file=args.output,
            model=args.model,
            max_tokens=args.max_tokens,
            format_type=args.format,
        )
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} {e}\n")
        return 1

    if args.json:
        print(json.dumps(pack_res.to_dict(), indent=2))
        return 0

    print(f"\n{BOLD}{GREEN}{CHECKMARK} Codebase successfully packed!{RESET}")
    print(f"  {BOLD}Source Directory:{RESET}   {pack_res.root_dir}")
    print(f"  {BOLD}Files Included:{RESET}     {pack_res.total_files:,}")
    print(f"  {BOLD}Total Tokens:{RESET}       {pack_res.total_tokens:,} {DIM}({pack_res.model}){RESET}")
    print(f"  {BOLD}Estimated Cost:{RESET}     ${pack_res.estimated_cost_usd:.6f}")
    if args.output:
        print(f"  {BOLD}Output Saved:{RESET}       {CYAN}{args.output}{RESET}")
    print(f"\n{BOLD}Top Files by Token Size:{RESET}")
    for stat in sorted(pack_res.file_stats, key=lambda s: s.tokens, reverse=True)[:5]:
        print(f"  - {stat.relative_path:<35} {stat.tokens:>7,d} tokens ({stat.pct_of_total:>5.1f}%)")
    print()
    return 0


def handle_check(args: argparse.Namespace) -> int:
    res = check_budget(
        target=args.target,
        model=args.model,
        max_cost_usd=args.max_cost,
        max_tokens=args.max_tokens,
        warning_cost_usd=args.warning_cost,
        completion_tokens=args.completion_tokens,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return res.exit_code

    if res.passed:
        print(f"\n{BOLD}{GREEN}{CHECKMARK} Budget check passed!{RESET}")
        print(f"  {BOLD}Target:{RESET}      {res.target}")
        print(f"  {BOLD}Tokens:{RESET}      {res.tokens:,} (model: {res.model})")
        print(f"  {BOLD}Est. Cost:{RESET}   ${res.cost_usd:.6f}")
        if res.has_warnings:
            for w in res.warnings:
                print(f"  {YELLOW}⚠ {w}{RESET}")
        print()
        return 0
    else:
        print(f"\n{BOLD}{RED}{CROSSMARK} Budget check FAILED!{RESET}")
        for v in res.violations:
            print(f"  {RED}• {v}{RESET}")
        print(f"  {BOLD}Current usage:{RESET} {res.tokens:,} tokens (~${res.cost_usd:.6f})\n")
        return 1


def handle_report(args: argparse.Namespace) -> int:
    rep = generate_report(
        target_path=args.target,
        output_format=args.format,
        model=args.model,
        completion_tokens=args.completion_tokens,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(rep)
        print(f"\n{BOLD}{GREEN}{CHECKMARK} Audit report generated:{RESET} {CYAN}{args.output}{RESET}\n")
    else:
        print(rep)
    return 0


def handle_ui(args: argparse.Namespace) -> int:
    start_server(port=args.port, host=args.host)
    return 0


def handle_mcp(args: argparse.Namespace) -> int:
    server = MCPServer()
    server.run_stdio()
    return 0


def handle_init_workflow(args: argparse.Namespace) -> int:
    try:
        wf = scaffold_github_workflow()
        print(f"\n{BOLD}{GREEN}{CHECKMARK} GitHub Actions budget gate created:{RESET} {CYAN}{wf}{RESET}\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} {e}\n")
        return 1


def handle_install_hook(args: argparse.Namespace) -> int:
    try:
        hook = install_git_precommit_hook()
        print(f"\n{BOLD}{GREEN}{CHECKMARK} Pre-commit hook installed:{RESET} {CYAN}{hook}{RESET}\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"{RED}Error:{RESET} {e}\n")
        return 1


def handle_models(args: argparse.Namespace) -> int:
    models = list_supported_models()

    if args.json:
        data = {m: MODEL_REGISTRY[m].__dict__ for m in models}
        print(json.dumps(data, indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== Supported Models & Pricing (per 1M tokens) ==={RESET}")
    header = f"{'MODEL':<20} {'PROVIDER':<14} {'INPUT ($)':<11} {'OUTPUT ($)':<12} {'CACHED ($)':<12} {'CONTEXT'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * len(header))

    for m in models:
        p = MODEL_REGISTRY[m]
        cached_str = f"${p.cached_input_per_m:.4f}" if p.cached_input_per_m is not None else "N/A"
        ctx_k = f"{p.context_window // 1000}k"
        print(
            f"{p.name:<20} {p.provider:<14} ${p.input_per_m:<10.4f} ${p.output_per_m:<11.4f} "
            f"{cached_str:<12} {ctx_k}"
        )
    print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tokentally",
        description="Fast Token Counter, Multi-Model Cost Estimator, Context Analyzer, Prompt Optimizer & MCP Server",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # count
    p_count = subparsers.add_parser("count", help="Count tokens in text, file, or stdin with tokenizer transparency")
    p_count.add_argument("target", nargs="?", default=None, help="Text string, file path, or - for stdin")
    p_count.add_argument("-m", "--model", default="gpt-4o", help="Target model for tokenizer (default: gpt-4o)")
    p_count.add_argument("--json", action="store_true", help="Output in JSON format")

    # cost
    p_cost = subparsers.add_parser("cost", help="Calculate exact inference dollar cost")
    p_cost.add_argument("target", nargs="?", default=None, help="Text string, file path, or - for stdin")
    p_cost.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate (default: gpt-4o)")
    p_cost.add_argument("--completion-tokens", type=int, default=0, help="Expected completion tokens")
    p_cost.add_argument("--cached-tokens", type=int, default=0, help="Tokens matching prompt cache")
    p_cost.add_argument("--json", action="store_true", help="Output in JSON format")

    # compare
    p_comp = subparsers.add_parser("compare", help="Compare cost across leading LLMs")
    p_comp.add_argument("target", nargs="?", default=None, help="Text string, file path, or - for stdin")
    p_comp.add_argument("--models", help="Comma-separated list of models to compare")
    p_comp.add_argument("--completion-ratio", type=float, default=0.5, help="Completion ratio relative to input")
    p_comp.add_argument("--json", action="store_true", help="Output in JSON format")

    # analyze
    p_ana = subparsers.add_parser("analyze", help="Decompose prompt layers (system, history, tools, RAG) & inspect caching")
    p_ana.add_argument("target", nargs="?", default=None, help="Prompt text, file, or JSON chat transcript")
    p_ana.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate")
    p_ana.add_argument("--json", action="store_true", help="Output in JSON format")

    # regression
    p_reg = subparsers.add_parser("regression", help="Audit token inflation between baseline and candidate prompts")
    p_reg.add_argument("baseline", help="Baseline prompt file or text")
    p_reg.add_argument("candidate", help="Candidate prompt file or text")
    p_reg.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate")
    p_reg.add_argument("--max-regression-pct", type=float, default=15.0, help="Maximum allowed token growth percentage")
    p_reg.add_argument("--json", action="store_true", help="Output in JSON format")

    # diff
    p_diff = subparsers.add_parser("diff", help="Profile token size and review cost of git changes")
    p_diff.add_argument("ref", nargs="?", default=None, help="Git branch or commit ref to diff against")
    p_diff.add_argument("--staged", action="store_true", help="Profile only git staged changes")
    p_diff.add_argument("--exclude-generated", action="store_true", default=False, help="Exclude lockfiles and compiled code from review")
    p_diff.add_argument("--ignore-generated", action="store_true", default=False, help="Alias for --exclude-generated")
    p_diff.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate")
    p_diff.add_argument("--json", action="store_true", help="Output in JSON format")

    # trace
    p_trc = subparsers.add_parser("trace", help="Audit agent step trajectories for repetitive loops and zero-progress cycles")
    p_trc.add_argument("target", help="JSON file or string containing array of agent steps")
    p_trc.add_argument("--json", action="store_true", help="Output in JSON format")

    # tools
    p_tls = subparsers.add_parser("tools", help="Audit tool schemas for excessive descriptions and field bloat")
    p_tls.add_argument("target", help="JSON file or string containing tool definitions")
    p_tls.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate")
    p_tls.add_argument("--json", action="store_true", help="Output in JSON format")

    # history
    p_his = subparsers.add_parser("history", help="Simulate multi-turn cumulative conversation history overhead O(n^2)")
    p_his.add_argument("--turns", type=int, default=10, help="Number of dialogue turns")
    p_his.add_argument("--tokens-per-turn", type=int, default=500, help="Average new tokens added per turn")
    p_his.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate")
    p_his.add_argument("--json", action="store_true", help="Output in JSON format")

    # pack
    p_pack = subparsers.add_parser("pack", help="Pack directory/codebase into LLM prompt context")
    p_pack.add_argument("directory", nargs="?", default=".", help="Root directory to pack (default: current dir)")
    p_pack.add_argument("-o", "--output", help="Output destination file (e.g. context.xml or prompt.md)")
    p_pack.add_argument("-m", "--model", default="gpt-4o", help="Model used for token calculation")
    p_pack.add_argument("--max-tokens", type=int, help="Maximum allowed token budget to include")
    p_pack.add_argument("--format", choices=["xml", "markdown"], default="xml", help="Packaging format (default: xml)")
    p_pack.add_argument("--json", action="store_true", help="Output summary in JSON format")

    # check
    p_check = subparsers.add_parser("check", help="CI/CD gate to verify token and cost budget limits")
    p_check.add_argument("target", help="File path, directory, or string prompt to evaluate")
    p_check.add_argument("-m", "--model", default=None, help="Model to evaluate (defaults to tokentally.toml)")
    p_check.add_argument("--max-cost", type=float, default=None, help="Maximum allowed cost in USD (e.g. 0.50)")
    p_check.add_argument("--warning-cost", type=float, default=None, help="Soft warning cost threshold")
    p_check.add_argument("--max-tokens", type=int, default=None, help="Maximum allowed tokens (e.g. 50000)")
    p_check.add_argument("--completion-tokens", type=int, default=0, help="Expected completion tokens")
    p_check.add_argument("--json", action="store_true", help="Output in JSON format")

    # optimize
    p_opt = subparsers.add_parser("optimize", help="Minify prompt with constraint invariance preservation")
    p_opt.add_argument("target", nargs="?", default=None, help="Prompt text or file path")
    p_opt.add_argument("-o", "--output", help="Destination file for optimized prompt")
    p_opt.add_argument("--strip-comments", action="store_true", help="Strip non-critical code comments")
    p_opt.add_argument("-m", "--model", default="gpt-4o", help="Model used for token calculation")
    p_opt.add_argument("--json", action="store_true", help="Output in JSON format")

    # report
    p_rep = subparsers.add_parser("report", help="Generate executive cost audit report (markdown or csv)")
    p_rep.add_argument("target", default=".", nargs="?", help="Target file or directory")
    p_rep.add_argument("--format", choices=["markdown", "csv"], default="markdown", help="Report format")
    p_rep.add_argument("-o", "--output", help="Save report to file")
    p_rep.add_argument("-m", "--model", default="gpt-4o", help="Primary model to evaluate")
    p_rep.add_argument("--completion-tokens", type=int, default=500, help="Expected completion tokens")

    # ui
    p_ui = subparsers.add_parser("ui", help="Launch interactive local web dashboard")
    p_ui.add_argument("--port", type=int, default=7860, help="Port to bind (default: 7860)")
    p_ui.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Start Model Context Protocol (MCP) stdio server")

    # init-workflow
    subparsers.add_parser("init-workflow", help="Scaffold GitHub Actions LLM budget gate workflow")

    # install-hook
    subparsers.add_parser("install-hook", help="Install git pre-commit budget guard hook")

    # models
    p_models = subparsers.add_parser("models", help="List all supported models and prices")
    p_models.add_argument("--json", action="store_true", help="Output in JSON format")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if not parsed_args.command:
        parser.print_help()
        return 0

    commands = {
        "count": handle_count,
        "cost": handle_cost,
        "compare": handle_compare,
        "analyze": handle_analyze,
        "regression": handle_regression,
        "diff": handle_diff,
        "tools": handle_tools,
        "history": handle_history,
        "trace": handle_trace,
        "pack": handle_pack,
        "check": handle_check,
        "optimize": handle_optimize,
        "report": handle_report,
        "ui": handle_ui,
        "mcp": handle_mcp,
        "init-workflow": handle_init_workflow,
        "install-hook": handle_install_hook,
        "models": handle_models,
    }

    handler = commands.get(parsed_args.command)
    if handler:
        return handler(parsed_args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
