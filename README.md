<div align="center">

# ⚡ TokenTally

**The ultimate developer toolkit for LLM token counting, multi-model cost estimation, codebase prompt packing, prompt optimization, git diff profiling, and CI/CD budget guardrails.**

[![PyPI Version](https://img.shields.io/pypi/v/tokentally.svg?color=blue)](https://pypi.org/project/tokentally/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tokentally.svg)](https://pypi.org/project/tokentally/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Pipeline](https://github.com/appu2712/tokentally/actions/workflows/ci.yml/badge.svg)](https://github.com/appu2712/tokentally/actions)
[![Downloads](https://img.shields.io/pypi/dm/tokentally.svg)](https://pypistats.org/packages/tokentally)
[![GitHub Stars](https://img.shields.io/github/stars/appu2712/tokentally?style=social)](https://github.com/appu2712/tokentally)

</div>

---

## 💡 Why TokenTally?

As LLMs power modern agent swarms, automated test suites, code reviewers, and production pipelines, **uncontrolled token consumption leads to surprising API bills and broken context windows**.

Developers and engineering teams need answers to fundamental questions:
* *How many tokens is this prompt or file across different model tokenizers?*
* *How much will this call actually cost on GPT-4o vs Claude 3.7 vs Gemini 2.5 vs DeepSeek V3?*
* *How can I pack my entire git repository into a structured prompt without exceeding limits?*
* *How much will this git pull request cost to review with an AI coding bot?*
* *How can I shrink prompt waste and redundant whitespace to save 20-30% on API costs?*
* *How can I block CI/CD runs from accidentally spending \$50 on runaway evaluation loops?*

**TokenTally** provides a unified, zero-dependency Python engine, high-speed CLI, interactive local web studio, and native Model Context Protocol (MCP) server that runs locally in milliseconds without requiring external API keys.

---

## 🚀 Key Features

* **⚡ Ultra-Fast Offline Tokenization**: Exact BPE encoding via `tiktoken` with calibrated zero-dependency heuristic fallback.
* **💰 Real-Time Multi-Model Pricing**: Verified pricing for 25+ models across **OpenAI** (`gpt-4o`, `o1`, `o3-mini`, `gpt-4o-mini`), **Anthropic** (`claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-haiku`), **Google** (`gemini-2.5-pro`, `gemini-2.5-flash`), **DeepSeek** (`deepseek-v3`, `deepseek-r1`), **Mistral** (`codestral`, `mistral-large`), **Groq LPUs**, and **Ollama (local)**.
* **🌐 Interactive Local Web Studio (`tokentally ui`)**: Built-in zero-dependency dark-mode visualizer with real-time sliders, comparison tables, and scenario simulations.
* **🤖 Native Model Context Protocol (MCP) Server (`tokentally mcp`)**: Plug TokenTally directly into Cursor, Claude Desktop, and Antigravity so your AI agents can budget their own tokens before spending money.
* **🔍 Git Diff AI Review Cost Profiler (`tokentally diff`)**: Profile staged changes, commits, or branch diffs to predict exact AI review costs before opening a PR.
* **📉 Prompt Minifier & Optimizer (`tokentally optimize`)**: Intelligently strips redundant whitespace, comments, and empty lines, reducing token consumption by up to 30%.
* **📦 Codebase Context Packer (`tokentally pack`)**: Repomix-compatible codebase bundler with `.gitignore` filtering and per-file token profiling.
* **🛡️ CI/CD Budget Guardrail (`tokentally check`)**: Enforce hard token and dollar limits in CI pipelines or pre-commit hooks to halt runaway spending.
* **🐍 Python SDK Tracking & Decorators**: `@tokentally.track` and `BudgetTracker` context managers for multi-call session spend observability.
* **📊 Multi-Format Audit Reports (`tokentally report`)**: Generate executive Markdown and CSV reports with volume projections for 1k, 10k, 100k calls/month.

---

## 📦 Installation

```bash
pip install tokentally
```

*Optional high-precision dev dependencies:*
```bash
pip install "tokentally[dev]"
```

---

## 💻 CLI Command Reference

### 1. Count Tokens
```bash
# Direct string
tokentally count "Explain the difference between attention mechanisms and SSMs"

# From a file
tokentally count ./src/main.py --model gpt-4o

# Piped from stdin
git diff | tokentally count -
```

### 2. Estimate Inference Cost
Calculate exact USD pricing including input, expected output, and prompt caching discounts:
```bash
tokentally cost ./prompts/analysis_task.txt --model gpt-4o --completion-tokens 500
```
```text
=== TokenTally Cost Estimation ===
  Model:            gpt-4o (OpenAI)
  Input Tokens:     1,240
  Output Tokens:    500
  Total Tokens:     1,740
  --------------------------------
  Input Cost:       $0.003100
  Output Cost:      $0.005000
  Total Cost:       $0.008100
```

### 3. Multi-Model Comparison Table
See how much your prompt costs across every major provider side-by-side:
```bash
tokentally compare ./prompts/analysis_task.txt
```
```text
=== Multi-Model Cost Comparison ===
MODEL                  PROVIDER       IN TOK    OUT TOK   TOTAL COST     RATIO
------------------------------------------------------------------------------
deepseek-v3            DeepSeek       1,240     620       $0.000347      0.04x
gemini-2.5-flash       Google         1,240     620       $0.000372      0.04x
gpt-4o-mini            OpenAI         1,240     620       $0.000558      0.06x
deepseek-r1            DeepSeek       1,240     620       $0.002040      0.22x
claude-3-5-haiku       Anthropic      1,240     620       $0.003472      0.37x
o3-mini                OpenAI         1,240     620       $0.004092      0.44x
gemini-2.5-pro         Google         1,240     620       $0.004650      0.50x
gpt-4o                 OpenAI         1,240     620       $0.009300      1.00x
claude-3-7-sonnet      Anthropic      1,240     620       $0.013020      1.40x
claude-3-5-sonnet      Anthropic      1,240     620       $0.013020      1.40x
o1                     OpenAI         1,240     620       $0.055800      6.00x
```

### 4. Git Diff AI Review Profiler
Analyze token size and estimated code review costs of uncommitted or staged changes:
```bash
# Check working tree changes
tokentally diff

# Check only staged changes
tokentally diff --staged --model gpt-4o

# Compare against main branch
tokentally diff main --model gpt-4o
```
```text
=== Git Diff AI Review Cost Profiler ===
  Target Ref:         working-tree
  Files Modified:     3
  Diff Patch Tokens:  7,878 (model: gpt-4o)
  Est. Review Cost:   $0.024695

FILE                                     TOKENS     CHANGES
-----------------------------------------------------------------
src/tokentally/__init__.py               595        +43/-2
src/tokentally/cli.py                    3,595      +170/-10
src/tokentally/models.py                 3,679      +125/-26
```

### 5. Prompt Optimizer & Minifier
Remove redundant whitespace, trailing spaces, and comments to shrink tokens:
```bash
tokentally optimize prompt.txt --output prompt_clean.txt --strip-comments
```
```text
[PASS] Prompt Optimization Complete!
  Original Tokens:   4,520 ($0.011300)
  Optimized Tokens:  3,110 ($0.007775)
  Tokens Saved:      1,410 (31.2% reduction)
  Per 10k Invocations: Saves $35.25
```

### 6. Codebase Context Packer
Pack an entire repository into structured XML or Markdown context for pasting into ChatGPT, Claude, or Gemini:
```bash
tokentally pack ./src --output context.xml --model gpt-4o
```

### 7. Interactive Local Web Studio
Launch the local web dashboard:
```bash
tokentally ui --port 7860
```
Open `http://localhost:7860` in your browser for real-time prompt drafting and interactive sliders.

### 8. CI/CD Budget Guardrail
Fail CI builds or pre-commit checks if prompts or contexts exceed your budget:
```bash
tokentally check ./prompts/system.txt --max-cost 0.20 --max-tokens 50000 --model gpt-4o
```

### 9. Instant Workflow Scaffolding
```bash
# Generate .github/workflows/tokentally-budget.yml
tokentally init-workflow

# Install .git/hooks/pre-commit
tokentally install-hook
```

---

## 🤖 Model Context Protocol (MCP) Integration

TokenTally includes a built-in MCP server. Connect it to **Cursor**, **Claude Desktop**, or **Antigravity**:

Add this to your `claude_desktop_config.json` or Cursor MCP settings:

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

Now your AI assistant has native access to:
* `tokentally_estimate_cost`
* `tokentally_compare_models`
* `tokentally_pack_workspace`
* `tokentally_optimize_prompt`

---

## 🐍 Python SDK Examples

```python
import tokentally as tt

# 1. Count tokens
tokens = tt.count_tokens("Explain quantum computing", model="gpt-4o")

# 2. Multi-model cost estimation
cost = tt.estimate_cost(tokens=12500, model="gpt-4o", completion_tokens=1000)
print(f"Cost: ${cost.total_cost_usd:.6f}")

# 3. Session Budget Tracking
with tt.BudgetTracker(max_budget_usd=1.00) as tracker:
    tracker.record("Prompt 1", completion="Answer 1", model="gpt-4o")
    tracker.record("Prompt 2", completion="Answer 2", model="o3-mini")

print(tracker.summary())

# 4. Function Decorator
@tt.track(model="gpt-4o", max_cost_usd=0.05)
def call_agent(prompt: str):
    return "LLM response..."

# 5. Optimize prompt text
clean = tt.optimize_prompt("messy   prompt\n\n\n\ntext", strip_comments=True)
print(f"Saved {clean.percent_reduction}% tokens")

# 6. Profile git diff
diff_summary = tt.profile_git_diff(staged=True)
print(f"Diff Tokens: {diff_summary.total_tokens}, Est. Review Cost: ${diff_summary.estimated_review_cost_usd:.4f}")
```

---

## 📋 Supported Models & Pricing Matrix

| Model | Provider | Input / 1M | Output / 1M | Cached / 1M | Context |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **gpt-4o** | OpenAI | \$2.50 | \$10.00 | \$1.25 | 128k |
| **gpt-4o-mini** | OpenAI | \$0.15 | \$0.60 | \$0.075 | 128k |
| **o1** | OpenAI | \$15.00 | \$60.00 | \$7.50 | 200k |
| **o1-mini** | OpenAI | \$1.10 | \$4.40 | \$0.55 | 128k |
| **o3-mini** | OpenAI | \$1.10 | \$4.40 | \$0.55 | 200k |
| **claude-3-7-sonnet** | Anthropic | \$3.00 | \$15.00 | \$0.30 | 200k |
| **claude-3-5-sonnet** | Anthropic | \$3.00 | \$15.00 | \$0.30 | 200k |
| **claude-3-5-haiku** | Anthropic | \$0.80 | \$4.00 | \$0.08 | 200k |
| **gemini-2.5-pro** | Google | \$1.25 | \$5.00 | \$0.3125 | 1000k |
| **gemini-2.5-flash** | Google | \$0.10 | \$0.40 | \$0.025 | 1000k |
| **deepseek-v3** | DeepSeek | \$0.14 | \$0.28 | \$0.014 | 64k |
| **deepseek-r1** | DeepSeek | \$0.55 | \$2.19 | \$0.14 | 64k |
| **codestral** | Mistral | \$0.30 | \$0.90 | N/A | 256k |
| **mistral-large** | Mistral | \$2.00 | \$6.00 | N/A | 128k |
| **groq-llama-3.3-70b**| Groq | \$0.59 | \$0.79 | N/A | 128k |
| **ollama-local** | Ollama | \$0.00 | \$0.00 | \$0.00 | 128k |

---

## 🤝 Contributing

Contributions are welcome! Check out [CONTRIBUTING.md](CONTRIBUTING.md) to add new models, customize pricing, or contribute features.

## 📄 License

TokenTally is open-source software licensed under the [MIT License](LICENSE).
