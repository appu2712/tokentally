<div align="center">

# ⚡ TokenTally

**The local-first AI resource optimization layer for LLM token counting, multi-model cost estimation, prompt decomposition, Git review value density, and CI/CD budget guardrails.**

[![PyPI Version](https://img.shields.io/pypi/v/tokentally.svg?color=blue)](https://pypi.org/project/tokentally/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tokentally.svg)](https://pypi.org/project/tokentally/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Pipeline](https://github.com/appu2712/tokentally/actions/workflows/ci.yml/badge.svg)](https://github.com/appu2712/tokentally/actions)
[![Downloads](https://img.shields.io/pypi/dm/tokentally.svg)](https://pypistats.org/packages/tokentally)
[![GitHub Stars](https://img.shields.io/github/stars/appu2712/tokentally?style=social)](https://github.com/appu2712/tokentally)

</div>

---

## The Problem

When engineering teams deploy autonomous agent loops, prompt templates, and AI code reviewers to production, token consumption is treated as an afterthought until the first multi-thousand dollar invoice arrives.

In production LLM systems:
1. **Prompts bloat silently**: Prompts grow from 400 tokens to 8,000 tokens as instructions and unranked RAG documents accumulate over time.
2. **Review tokens are wasted**: AI code review bots burn 80% of their token budget reviewing minified JavaScript bundles and lockfiles (`package-lock.json`, `poetry.lock`).
3. **Caches break invisibly**: Dynamic timestamps or UUIDs placed at line 1 invalidate prompt caching, forfeiting 50–90% provider discounts on every single call.
4. **Agent histories compound quadratically**: Multi-turn dialogue resends historical context every step, accumulating $O(n^2)$ token overhead across long sessions.
5. **No build-time gates**: A developer modifying a system prompt can introduce a 300% cost regression without failing any existing unit tests.

**TokenTally** provides a local-first, zero-dependency Python library, CLI, local web studio, and native Model Context Protocol (MCP) server to measure, explain, profile, and enforce token economics before requests ever touch an external API.

---

## Core Capabilities

| Capability | Command | What It Solves |
| :--- | :--- | :--- |
| **Token Counting** | `tokentally count` | Dual BPE (`tiktoken`) + calibrated heuristic fallback with exact method transparency. |
| **Inference Cost** | `tokentally cost` | Exact USD pricing calculating input, completion, and prompt cache hit rates. |
| **Model Comparison** | `tokentally compare` | Instant side-by-side cost matrix across 25+ models from OpenAI, Anthropic, Google, DeepSeek, Mistral, Meta, Cohere, Bedrock, and Cerebras. |
| **Context Attribution** | `tokentally analyze` | Decomposes prompts into layers (system, tools, user, history, RAG), checks static cache prefixes, and projects reasoning tokens. |
| **Git Review Density**| `tokentally diff` | Classifies diff files into human vs generated vs lockfiles; computes Review Value Density. |
| **Regression Gates** | `tokentally regression` | Compares candidate prompts against stored baselines or historical git refs (`git:main:prompt.txt`). |
| **Tool Schema Audit** | `tokentally tools` | Measures JSON Schema token footprint, field depth, and parameter description bloat. |
| **History Simulator**| `tokentally history` | Calculates cumulative $O(n^2)$ conversation token growth across dialogue turns. |
| **Agent Trace Audit** | `tokentally trace` | Detects zero-progress cycles, repetitive tool calls, and runaway agent loops. |
| **Codebase Packer** | `tokentally pack` | Bundles directories into structured XML/Markdown context prompts with `.gitignore` filtering. |
| **Prompt Optimizer** | `tokentally optimize` | Constraint-invariant minification stripping whitespace and redundant comments without altering instructions. |
| **CI/CD Guardrail** | `tokentally check` | Hard exit-code budget gate for GitHub Actions and pre-commit hooks based on `tokentally.toml`. |
| **Local Web Studio** | `tokentally ui` | Zero-dependency dark-mode visualizer with real-time sliders and comparison tables. |
| **MCP Server** | `tokentally mcp` | JSON-RPC 2.0 interface exposing 10 tools to Cursor, Claude Desktop, and Antigravity. |

---

## Installation

```bash
# Core package (zero dependencies required, pure Python standard library)
pip install tokentally

# Optional: with tiktoken for exact OpenAI BPE tokenization
pip install "tokentally[dev]"
```

---

## Command Reference

### 1. Count Tokens
Counts tokens across files, raw text, or piped standard input:
```bash
# Raw text
tokentally count "Explain the Raft consensus protocol in distributed databases"

# Specific file
tokentally count ./src/main.py --model gpt-4o

# Read from stdin
git diff | tokentally count -
```

### 2. Estimate Inference Cost
Calculates billable input, completion, and cached token pricing:
```bash
tokentally cost ./prompts/system.txt --model gpt-4o --completion-tokens 500 --cached-tokens 1000
```
```text
=== TokenTally Cost Estimation ===
  Model:            gpt-4o (OpenAI)
  Input Tokens:     2,450
  Cached Tokens:    1,000 (cached rate applied)
  Output Tokens:    500
  Total Tokens:     2,950
  --------------------------------
  Input Cost:       $0.003625
  Cached Cost:      $0.001250
  Output Cost:      $0.005000
  Total Cost:       $0.009875
```

### 3. Compare Across Providers
Compares dollar costs side-by-side against the cheapest baseline:
```bash
tokentally compare ./prompts/analysis.txt
```
```text
=== Multi-Model Cost Comparison ===
MODEL                  PROVIDER       IN TOK    OUT TOK   TOTAL COST     RATIO
------------------------------------------------------------------------------
deepseek-v3            DeepSeek       1,840     920       $0.000515      0.04x
gemini-2.5-flash       Google         1,840     920       $0.000552      0.04x
gpt-4o-mini            OpenAI         1,840     920       $0.000828      0.06x
command-r              Cohere         1,840     920       $0.000828      0.06x
cerebras-llama-3.3-70b Cerebras       1,840     920       $0.001656      0.12x
deepseek-r1            DeepSeek       1,840     920       $0.003027      0.22x
claude-3-5-haiku       Anthropic      1,840     920       $0.005152      0.37x
o3-mini                OpenAI         1,840     920       $0.006072      0.44x
gemini-2.5-pro         Google         1,840     920       $0.006900      0.50x
gpt-4o                 OpenAI         1,840     920       $0.013800      1.00x
claude-3-5-sonnet      Anthropic      1,840     920       $0.019320      1.40x
claude-3-7-sonnet      Anthropic      1,840     920       $0.019320      1.40x
o1                     OpenAI         1,840     920       $0.082800      6.00x
```

### 4. Context Decomposition & Prompt Caching Audit
Inspects prompt layer attribution and verifies prompt caching eligibility:
```bash
tokentally analyze ./prompts/chat_context.json --model gpt-4o --output audit.md
```
```text
=== TokenTally Context & Bloat Audit ===
  Total Tokens:       4,250 [exact BPE: o200k_base]
  Model Evaluated:    gpt-4o ($0.010625/call)

Context Components Attribution:
  LAYER                    TOKENS    DISTRIBUTION       PERCENT   EST. COST    CACHEABLE
  ----------------------------------------------------------------------------------------
  system_instructions      1,200     [####----------]   28.2%     $0.003000    Yes
  tool_definitions         1,850     [######--------]   43.5%     $0.004625    Yes
  rag_context              800       [###-----------]   18.8%     $0.002000    No
  user_request             400       [#-------------]   9.4%      $0.001000    No

Prompt Caching Analysis:
  Static Prefix Tokens:   3,050
  Dynamic Tokens:        1,200
  Cache Status:          Eligible
  Estimated Hit Rate:    71.8%
  Recommendation:        Static prefix meets minimum threshold (1,024 tokens). Expected 50-90% caching discount applied.
```

### 5. Git Diff AI Review Profiler
Profiles git changes to calculate Review Value Density before opening a PR:
```bash
# Check working tree
tokentally diff

# Profile only human logic changes, excluding package-lock.json and autogenerated files
tokentally diff main --exclude-generated --output pr_review_cost.md
```
```text
=== Git Diff AI Review Cost Profiler ===
  Target Ref:           main
  Files Modified:       5
  Effective Review Tokens: 4,120 (model: gpt-4o)
  Human Logic Tokens:   3,850
  Generated/Lock Tokens:270
  Review Value Density: 93.4%
  Estimated Review Cost:$0.010300
```

### 6. Prompt Token Regression Gate
Ensures prompt modifications do not inflate token counts beyond a threshold:
```bash
# Compare working file against a git branch or commit
tokentally regression git:main:prompts/system.txt prompts/system.txt --max-regression-pct 15.0
```
```text
=== Prompt Token Regression Audit ===
  Baseline Tokens:    1,200 ($0.003000)
  Candidate Tokens:   1,320 ($0.003300)
  Token Delta:        +120 tokens (+10.0%)
  Monthly Cost Impact:+$3.00 / 10k calls

[PASS] Token change (+10.0%) is within allowed threshold (+15.0%).
```

### 7. Tool Schema Audit
Audits function definitions to identify parameter bloat:
```bash
tokentally tools ./agent_tools.json
```
```text
=== Tool Schema Context & Bloat Audit ===
  Total Tools Exposed:  12
  Total Schema Tokens:  2,840
  Fixed Overhead/Call:  $0.007100

TOOL NAME                      TOKENS     FIELDS   DEPTH    DESC %
-----------------------------------------------------------------
database_query_tool            820        14       3         62.4%
fetch_customer_record          640        9        2         54.1%
calculator                     110        2        1         32.0%
```

### 8. Multi-Turn Cumulative History Simulator
Simulates the $O(n^2)$ reprocessing multiplier of multi-turn dialogues:
```bash
tokentally history --turns 15 --tokens-per-turn 400
```
```text
=== Multi-Turn History O(n^2) Cumulative Growth Simulation ===
  Dialogue Turns:            15
  Tokens added/turn:         400
  Final Single-Turn Context: 6,000 tokens ($0.015000)
  Cumulative Processed:     48,000 tokens ($0.120000)
  Reprocessing Multiplier:  8.0x overhead

  Recommendation: Over 15 turns, naive history re-sending forces the model to process 48,000 cumulative tokens (8.0x the final 6,000 token state). Compressing historical turns into a state object saves $0.1050 per session.
```

### 9. Prompt Minifier & Optimizer
Minifies prompts by stripping redundant whitespace and comments with guaranteed constraint invariance:
```bash
tokentally optimize prompt.txt --output prompt_min.txt --strip-comments
```
```text
[PASS] Prompt Optimization Complete! [Invariance: 100% Passed]
  Original Tokens:   3,450 ($0.008625)
  Optimized Tokens:  2,520 ($0.006300)
  Tokens Saved:      930 (27.0% reduction)
  Per 10k Invocations: Saves $23.25
```

### 10. Codebase Context Packer
Packs files into a structured XML or Markdown prompt respecting `.gitignore` and `.tokentallyignore`:
```bash
tokentally pack ./src --output context.xml --max-tokens 50000 --ignore "tests/*,*.log"
```

### 11. Custom Model Management
Register proprietary internal or fine-tuned models:
```bash
# Register a custom fine-tune
tokentally models --add my-company-model --provider Internal --input 0.50 --output 1.50 --cached 0.10

# Remove when deprecated
tokentally models --remove my-company-model
```

---

## Configuration (`tokentally.toml`)

Tokentally reads policies declaratively from `tokentally.toml`:

```toml
[budget]
default_model = "gpt-4o"
max_prompt_tokens = 60000
max_cost_per_request = 0.25
warning_cost_usd = 0.10

[regression]
baseline_file = "prompts/system_v1.txt"
max_regression_pct = 12.0
fail_on_regression = true

[review]
max_review_tokens = 40000
exclude_lockfiles = true
exclude_generated = true

# Register private or fine-tuned model pricing
[custom_models.internal_llama]
provider = "Internal Infrastructure"
input_per_m = 0.40
output_per_m = 1.20
cached_input_per_m = 0.08
context_window = 32768
description = "Internal fine-tuned LLaMA-3 model"
```

---

## Model Context Protocol (MCP) Integration

Tokentally includes a native stdio JSON-RPC 2.0 MCP server. Connect it to **Cursor**, **Claude Desktop**, or **Antigravity**:

Add this to your `claude_desktop_config.json` or Cursor MCP configuration:

```json
{
  "mcpServers": {
    "tokentally": {
      "command": "tokentally",
      "args": ["mcp"]
    }
  }
}
```

Exposed MCP tools:
* `tokentally_estimate_cost`
* `tokentally_compare_models`
* `tokentally_analyze_context`
* `tokentally_profile_git_diff`
* `tokentally_check_regression`
* `tokentally_inspect_tools`
* `tokentally_simulate_history`
* `tokentally_audit_agent_trace`
* `tokentally_pack_workspace`
* `tokentally_optimize_prompt`

---

## Python SDK Examples

```python
import tokentally as tt

# 1. High-precision or heuristic token count
result = tt.count_tokens_detailed("Explain vector databases", model="gpt-4o")
print(f"Tokens: {result.tokens} (Method: {result.method}, Exact: {result.is_exact})")

# 2. Multi-model cost estimation
cost = tt.estimate_cost("Prompt text...", model="claude-3-5-sonnet", completion_tokens=800)
print(f"Total Call Cost: ${cost.total_cost_usd:.6f}")

# 3. Context layer decomposition
analysis = tt.analyze_prompt_context(prompt_text, model="gpt-4o")
print(f"Cache Hit Rate: {analysis.cacheability.estimated_cache_hit_rate_pct}%")

# 4. Invariance-preserving optimization
minified = tt.optimize_prompt(prompt_text, strip_comments=True)
print(f"Saved {minified.percent_reduction}% tokens without touching constraints")

# 5. Session budget tracking context manager
with tt.BudgetTracker(max_budget_usd=1.00) as tracker:
    tracker.record(prompt="Task 1", completion="Output 1", model="gpt-4o")
    tracker.record(prompt="Task 2", completion="Output 2", model="deepseek-v3")

print(tracker.summary())

# 6. Function decorator guardrail
@tt.track(model="gpt-4o", max_cost_usd=0.05)
def call_agent_pipeline(query: str):
    return "LLM result"
```

---

## Supported Models & Pricing Matrix (USD per 1M tokens)

| Model Identifier | Provider | Input ($) | Output ($) | Cached ($) | Context Window |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **gpt-4o** | OpenAI | \$2.5000 | \$10.0000 | \$1.2500 | 128k |
| **gpt-4o-mini** | OpenAI | \$0.1500 | \$0.6000 | \$0.0750 | 128k |
| **o1** | OpenAI | \$15.0000 | \$60.0000 | \$7.5000 | 200k |
| **o1-mini** | OpenAI | \$1.1000 | \$4.4000 | \$0.5500 | 128k |
| **o3-mini** | OpenAI | \$1.1000 | \$4.4000 | \$0.5500 | 200k |
| **claude-3-7-sonnet** | Anthropic | \$3.0000 | \$15.0000 | \$0.3000 | 200k |
| **claude-3-5-sonnet** | Anthropic | \$3.0000 | \$15.0000 | \$0.3000 | 200k |
| **claude-3-5-haiku** | Anthropic | \$0.8000 | \$4.0000 | \$0.0800 | 200k |
| **claude-3-opus** | Anthropic | \$15.0000 | \$75.0000 | \$1.5000 | 200k |
| **gemini-2.5-pro** | Google | \$1.2500 | \$5.0000 | \$0.3125 | 1000k |
| **gemini-2.5-flash** | Google | \$0.1000 | \$0.4000 | \$0.0250 | 1000k |
| **gemini-2.0-flash** | Google | \$0.1000 | \$0.4000 | \$0.0250 | 1000k |
| **deepseek-v3** | DeepSeek | \$0.1400 | \$0.2800 | \$0.0140 | 64k |
| **deepseek-r1** | DeepSeek | \$0.5500 | \$2.1900 | \$0.1400 | 64k |
| **codestral** | Mistral | \$0.3000 | \$0.9000 | N/A | 256k |
| **mistral-large** | Mistral | \$2.0000 | \$6.0000 | N/A | 128k |
| **command-r** | Cohere | \$0.1500 | \$0.6000 | \$0.0750 | 128k |
| **command-r-plus** | Cohere | \$2.5000 | \$10.0000 | \$1.2500 | 128k |
| **bedrock-claude-3-5** | AWS Bedrock | \$3.0000 | \$15.0000 | \$0.3000 | 200k |
| **bedrock-nova-pro** | AWS Bedrock | \$0.8000 | \$3.2000 | \$0.2000 | 300k |
| **bedrock-nova-lite** | AWS Bedrock | \$0.0600 | \$0.2400 | \$0.0150 | 300k |
| **cerebras-llama-3.3-70b**| Cerebras | \$0.6000 | \$0.6000 | N/A | 128k |
| **groq-llama-3.3-70b** | Groq | \$0.5900 | \$0.7900 | N/A | 128k |
| **qwen-2.5-coder-32b** | Alibaba / Open | \$0.2000 | \$0.2000 | N/A | 128k |
| **llama-3.3-70b** | Meta / Open | \$0.7000 | \$0.8000 | N/A | 128k |
| **ollama-local** | Ollama | \$0.0000 | \$0.0000 | \$0.0000 | 128k |
| **vllm-local** | vLLM | \$0.0000 | \$0.0000 | \$0.0000 | 128k |

---

## Further Documentation

* [🔬 Empirical Research Foundations](docs/research_foundations.md): The papers and benchmarks behind Tokentally (FrugalGPT, LLMLingua, Lost in the Middle, PagedAttention, KV-caching).
* [🏗️ Architecture & Component Design](docs/ARCHITECTURE.md): System invariants, data structures, and the zero-dependency execution model.

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for testing guidelines and guidelines on submitting model pricing updates.

## License

Tokentally is open-source software licensed under the [MIT License](LICENSE).
