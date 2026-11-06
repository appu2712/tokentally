"""
Command-line interface for tokentally.
"""

import argparse
import json
import os
import sys
from typing import List, Optional

from . import __version__
from .counter import count_tokens
from .calculator import estimate_cost, compare_models
from .packer import pack_repository
from .guard import check_budget
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


def _read_input_target(target: Optional[str]) -> str:
    """Read content from target argument, stdin pipe, or file."""
    if target and target != "-":
        if os.path.isfile(target):
            with open(target, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return target

    # Read from standard input if piped
    if not sys.stdin.isatty():
        return sys.stdin.read()

    if target == "-":
        return sys.stdin.read()

    return ""


def handle_count(args: argparse.Namespace) -> int:
    content = _read_input_target(args.target)
    if not content:
        sys.stderr.write(f"{RED}Error:{RESET} No input text, file, or piped content provided.\n")
        return 1

    tokens = count_tokens(content, model=args.model)

    if args.json:
        print(json.dumps({"target": args.target or "stdin", "model": args.model, "tokens": tokens}, indent=2))
    else:
        print(f"{BOLD}Tokens:{RESET} {CYAN}{tokens:,}{RESET} {DIM}(model: {args.model}){RESET}")
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
    header = f"{'MODEL':<22} {'PROVIDER':<12} {'IN TOK':<9} {'OUT TOK':<9} {'TOTAL COST':<14} {'RATIO'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * len(header))

    for r in rows:
        ratio_str = f"{r.relative_ratio:.2f}x"
        color = GREEN if r.relative_ratio <= 1.0 else YELLOW if r.relative_ratio < 5.0 else RED
        print(
            f"{r.model:<22} {r.provider:<12} {r.input_tokens:<9,d} {r.output_tokens:<9,d} "
            f"{color}${r.total_cost_usd:<13.6f}{RESET} {DIM}{ratio_str}{RESET}"
        )
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
        completion_tokens=args.completion_tokens,
    )

    if args.json:
        print(json.dumps(res.to_dict(), indent=2))
        return res.exit_code

    if res.passed:
        print(f"\n{BOLD}{GREEN}{CHECKMARK} Budget check passed!{RESET}")
        print(f"  {BOLD}Target:{RESET}      {res.target}")
        print(f"  {BOLD}Tokens:{RESET}      {res.tokens:,} (model: {res.model})")
        print(f"  {BOLD}Est. Cost:{RESET}   ${res.cost_usd:.6f}\n")
        return 0
    else:
        print(f"\n{BOLD}{RED}{CROSSMARK} Budget check FAILED!{RESET}")
        for v in res.violations:
            print(f"  {RED}• {v}{RESET}")
        print(f"  {BOLD}Current usage:{RESET} {res.tokens:,} tokens (~${res.cost_usd:.6f})\n")
        return 1


def handle_models(args: argparse.Namespace) -> int:
    models = list_supported_models()

    if args.json:
        data = {m: MODEL_REGISTRY[m].__dict__ for m in models}
        print(json.dumps(data, indent=2))
        return 0

    print(f"\n{BOLD}{CYAN}=== Supported Models & Pricing (per 1M tokens) ==={RESET}")
    header = f"{'MODEL':<20} {'PROVIDER':<12} {'INPUT ($)':<11} {'OUTPUT ($)':<12} {'CACHED ($)':<12} {'CONTEXT'}"
    print(f"{BOLD}{header}{RESET}")
    print("-" * len(header))

    for m in models:
        p = MODEL_REGISTRY[m]
        cached_str = f"${p.cached_input_per_m:.4f}" if p.cached_input_per_m is not None else "N/A"
        ctx_k = f"{p.context_window // 1000}k"
        print(
            f"{p.name:<20} {p.provider:<12} ${p.input_per_m:<10.4f} ${p.output_per_m:<11.4f} "
            f"{cached_str:<12} {ctx_k}"
        )
    print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tokentally",
        description="Fast Token Counter, LLM Cost Estimator, Context Packer & Budget Guardrail",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # count
    p_count = subparsers.add_parser("count", help="Count tokens in text, file, or stdin")
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
    p_check.add_argument("-m", "--model", default="gpt-4o", help="Model to evaluate")
    p_check.add_argument("--max-cost", type=float, help="Maximum allowed cost in USD (e.g. 0.50)")
    p_check.add_argument("--max-tokens", type=int, help="Maximum allowed tokens (e.g. 50000)")
    p_check.add_argument("--completion-tokens", type=int, default=0, help="Expected completion tokens")
    p_check.add_argument("--json", action="store_true", help="Output in JSON format")

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
        "pack": handle_pack,
        "check": handle_check,
        "models": handle_models,
    }

    handler = commands.get(parsed_args.command)
    if handler:
        return handler(parsed_args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
