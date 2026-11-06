# 🏗️ Architecture & Design Philosophy

Tokentally is engineered to be an **AI resource optimization layer** that runs before network requests are dispatched.

```
                              ┌────────────────────────┐
                              │  User Prompt / Codebase │
                              └───────────┬────────────┘
                                          │
                     ┌────────────────────┴────────────────────┐
                     ▼                                         ▼
            [ Tokenizer Engine ]                      [ Context Decomposer ]
          exact BPE or calibrated regex              system, tools, history, RAG
                     │                                         │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                                [ Cost & FinOps Engine ]
                           25+ models, caching rates, reasoning
                                          │
         ┌──────────────────┬─────────────┴────────────┬──────────────────┐
         ▼                  ▼                          ▼                  ▼
  [ CI/CD Guard ]    [ MCP Server ]             [ Local Studio ]    [ Git Diff Review ]
  hard gates, exit   Cursor, Claude,            port 7860           lockfile filter,
  codes, regressions Antigravity                zero-dep UI         review density
```

---

## Core Tenets

### 1. Zero Required Dependencies
The entire core of Tokentally (`tokentally count`, `cost`, `compare`, `analyze`, `diff`, `pack`, `check`, `optimize`, `mcp`, `ui`) executes on the Python standard library alone. 
- High-precision BPE tokenization optionally uses `tiktoken` when installed. If absent, Tokentally uses a calibrated Unicode regex tokenizer calibrated to within 3–5% of exact token counts.
- Configuration uses `tomllib` in Python 3.11+ and a built-in fallback parser on older runtimes.
- Local Studio (`tokentally ui`) runs via `http.server` and standard Web APIs.
- MCP Server (`tokentally mcp`) communicates via standard JSON-RPC 2.0 over `stdin` and `stdout`.

### 2. Understand Before Optimizing
Tokentally follows the principle: **Measure → Explain → Recommend → Optimize → Enforce**.
Before changing a single character in a prompt or stripping a file from a git diff, Tokentally presents:
1. Exact token and cost deltas.
2. Attribution breakdown across layers.
3. Constraint verification guarantees.

### 3. Local-First and Privacy-Preserving
Tokentally never transmits prompt text or codebase contents to external servers or telemetry endpoints. All tokenization, caching analysis, and diff classification take place on your local machine.

---

## Component Responsibilities

| Module | File | Key Functions / Classes | Responsibility |
| :--- | :--- | :--- | :--- |
| **Token Counter** | `counter.py` | `TokenCounter`, `count_tokens_detailed` | Hybrid BPE / Regex counting with method transparency (`exact_bpe` vs `calibrated_heuristic`). |
| **Model Registry** | `models.py` | `MODEL_REGISTRY`, `normalize_model_name`, `save_custom_model` | Pricing per 1M tokens, prompt cache discounts, context limits, date and hub prefix normalization. |
| **Cost Calculator** | `calculator.py` | `CostCalculator`, `estimate_cost`, `compare_models` | Exact dollar calculations, multi-model sorting, and ratio baselines. |
| **Context Analyzer**| `analyzer.py` | `PromptContextAnalyzer`, `analyze_prompt_context` | Structural layer decomposition, dynamic cache-breaker detection, reasoning token projections. |
| **Git Review** | `git.py` | `GitDiffProfiler`, `profile_git_diff` | File classification (human vs lockfile vs generated), Review Value Density calculation. |
| **Budget Guard** | `guard.py` | `BudgetGuard`, `check_budget` | Soft warning thresholds and hard build-breaking CI gates. |
| **Regression Gate**| `regression.py` | `RegressionComparator`, `compare_prompt_regression` | Detects token inflation against baseline files or historical git revisions (`git:ref:path`). |
| **Tool Inspector** | `tools.py` | `ToolWorkloadEngine`, `analyze_tool_schemas` | JSON Schema token measurement, history growth simulation, loop trajectory detection. |
| **Prompt Optimizer**| `optimizer.py` | `PromptOptimizer`, `optimize_prompt` | Constraint-invariant minification with negative rule preservation. |
| **Repo Packer** | `packer.py` | `RepositoryPacker`, `pack_repository` | Multi-file XML/Markdown context assembly respecting `.gitignore` and `.tokentallyignore`. |
| **MCP Server** | `mcp.py` | `MCPServer`, `TOOLS_METADATA` | JSON-RPC 2.0 interface exposing 10 tools to Cursor, Claude Desktop, and Antigravity. |
| **Studio UI** | `server.py` | `start_server`, `DashboardRequestHandler` | Zero-dependency local web app with live sliders and side-by-side cost comparisons. |
