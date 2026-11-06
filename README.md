<div align="center">

# ⚡ TokenTally

**Blazingly fast token counter, multi-model cost estimator, codebase context packer, and CI/CD budget guardrail for LLM applications.**

[![PyPI Version](https://img.shields.io/pypi/v/tokentally.svg?color=blue)](https://pypi.org/project/tokentally/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tokentally.svg)](https://pypi.org/project/tokentally/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI Pipeline](https://github.com/apra-acharya/tokentally/actions/workflows/ci.yml/badge.svg)](https://github.com/apra-acharya/tokentally/actions)
[![Downloads](https://img.shields.io/pypi/dm/tokentally.svg)](https://pypistats.org/packages/tokentally)
[![GitHub Stars](https://img.shields.io/github/stars/apra-acharya/tokentally?style=social)](https://github.com/apra-acharya/tokentally)

</div>

---

## 💡 Why TokenTally?

As LLMs power more production pipelines, CI/CD test suites, and coding agents, **uncontrolled token consumption leads to surprising API bills**.

Developers and teams need answers to simple questions:
* *How many tokens is this prompt or file across different model tokenizers?*
* *How much will this actually cost on GPT-4o vs Claude 3.7 vs Gemini 2.5 vs DeepSeek V3?*
* *How can I pack my git repository into a structured prompt without blowing past context limits?*
* *How can I block CI/CD runs from accidentally spending \$50 on runaway eval loops?*

**TokenTally** solves this with a unified, lightweight Python library and CLI that works offline in milliseconds without API keys.

---

## 🚀 Key Features

* **⚡ Ultra-Fast Offline Tokenization**: Exact BPE encoding via `tiktoken` with calibrated zero-dependency heuristic fallback.
* **💰 Real-Time Multi-Model Pricing**: Verified pricing for 20+ models across **OpenAI** (`gpt-4o`, `o1`, `o3-mini`, `gpt-4o-mini`), **Anthropic** (`claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-haiku`), **Google** (`gemini-2.5-pro`, `gemini-2.5-flash`), and **DeepSeek** (`deepseek-v3`, `deepseek-r1`).
* **📦 Codebase Context Packer**: Pack repositories into structured XML or Markdown contexts with automatic `.gitignore` parsing, binary filtering, and per-file token breakdowns.
* **🛡️ CI/CD Budget Guardrail**: Enforce hard token and dollar limits in CI pipelines or pre-commit hooks to halt runaway spending.
* **📊 Multi-Model Cost Matrix**: Side-by-side cost comparisons and relative cost ratios with a single command.
* **🔌 Zero Network Latency**: Runs 100% locally with zero external network requests required.

---

## 📦 Installation

```bash
pip install tokentally
```

*Optional high-precision tokenizer:*
```bash
pip install "tokentally[dev]"
```

---

## 💻 CLI Quickstart

### 1. Count Tokens
Count tokens from strings, files, or standard input:
```bash
# Direct string
tokentally count "Explain the difference between attention mechanisms and SSMs"

# From a file
tokentally count ./src/main.py --model gpt-4o

# Piped from git diff
git diff | tokentally count
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

### 3. Compare Cost Across Leading LLMs
See how much your prompt costs across every major provider:
```bash
tokentally compare ./prompts/analysis_task.txt
```
```text
=== Multi-Model Cost Comparison ===
MODEL                  PROVIDER     IN TOK    OUT TOK   TOTAL COST     RATIO
----------------------------------------------------------------------------
deepseek-v3            DeepSeek     1,240     620       $0.000347      0.04x
gemini-2.5-flash       Google       1,240     620       $0.000372      0.04x
gpt-4o-mini            OpenAI       1,240     620       $0.000558      0.06x
deepseek-r1            DeepSeek     1,240     620       $0.002040      0.22x
claude-3-5-haiku       Anthropic    1,240     620       $0.003472      0.37x
o3-mini                OpenAI       1,240     620       $0.004092      0.44x
gemini-2.5-pro         Google       1,240     620       $0.004650      0.50x
gpt-4o                 OpenAI       1,240     620       $0.009300      1.00x
claude-3-7-sonnet      Anthropic    1,240     620       $0.013020      1.40x
claude-3-5-sonnet      Anthropic    1,240     620       $0.013020      1.40x
o1                     OpenAI       1,240     620       $0.055800      6.00x
```

### 4. Pack a Codebase for LLMs
Pack an entire repository into clean XML or Markdown format for pasting into ChatGPT, Claude, or Gemini:
```bash
tokentally pack ./src --output context.xml --model gpt-4o
```
```text
[PASS] Codebase successfully packed!
  Source Directory:   ./src
  Files Included:     8
  Total Tokens:       12,578 (gpt-4o)
  Estimated Cost:     $0.031445
  Output Saved:       context.xml

Top Files by Token Size:
  - cli.py                  3,583 tokens ( 28.5%)
  - packer.py               2,575 tokens ( 20.5%)
  - models.py               2,386 tokens ( 19.0%)
```

### 5. CI/CD Budget Guardrail
Fail CI builds or pre-commit checks if prompts or contexts exceed your budget:
```bash
# Fail if prompt costs more than $0.20 or exceeds 50,000 tokens
tokentally check ./prompts/system.txt --max-cost 0.20 --max-tokens 50000 --model gpt-4o
```

---

## 🐍 Python API

TokenTally can be imported as a lightweight Python library in any script, service, or agent:

```python
import tokentally as tt

# 1. Count tokens
tokens = tt.count_tokens("Hello world from TokenTally!", model="gpt-4o")
print(f"Tokens: {tokens}")

# 2. Estimate cost
cost = tt.estimate_cost(tokens=12500, model="gpt-4o", completion_tokens=1000)
print(f"Total: ${cost.total_cost_usd:.6f}")
print(f"Input: ${cost.input_cost_usd:.6f}")
print(f"Output: ${cost.output_cost_usd:.6f}")

# 3. Multi-model comparison
comparison = tt.compare_models("Explain quantum entanglement in simple terms.")
for row in comparison:
    print(f"{row.model:<20} ${row.total_cost_usd:.6f} ({row.relative_ratio}x)")

# 4. Pack directory for LLM prompt
pack = tt.pack_repository("./my_project", format_type="xml")
print(f"Packed {pack.total_files} files with {pack.total_tokens} tokens.")
pack.write_to("llm_prompt.xml")

# 5. Budget check
guard = tt.check_budget("./prompt.txt", model="gpt-4o", max_cost_usd=0.10)
if not guard.passed:
    raise ValueError(f"Budget exceeded: {guard.violations}")
```

---

## 🛡️ GitHub Actions CI Integration

Add TokenTally to your `.github/workflows/ai-evals.yml` to prevent costly eval runs:

```yaml
name: AI Evaluation Budget Gate

on: [pull_request]

jobs:
  budget-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install TokenTally
        run: pip install tokentally

      - name: Enforce Budget Limit
        run: |
          tokentally check ./evals/test_prompts.txt --max-cost 0.50 --model gpt-4o
```

---

## 📋 Supported Models & Pricing Matrix

| Model | Provider | Input / 1M | Output / 1M | Cached / 1M | Context |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **gpt-4o** | OpenAI | \$2.50 | \$10.00 | \$1.25 | 128k |
| **gpt-4o-mini** | OpenAI | \$0.15 | \$0.60 | \$0.075 | 128k |
| **o1** | OpenAI | \$15.00 | \$60.00 | \$7.50 | 200k |
| **o3-mini** | OpenAI | \$1.10 | \$4.40 | \$0.55 | 200k |
| **claude-3-7-sonnet** | Anthropic | \$3.00 | \$15.00 | \$0.30 | 200k |
| **claude-3-5-sonnet** | Anthropic | \$3.00 | \$15.00 | \$0.30 | 200k |
| **claude-3-5-haiku** | Anthropic | \$0.80 | \$4.00 | \$0.08 | 200k |
| **gemini-2.5-pro** | Google | \$1.25 | \$5.00 | \$0.3125 | 1000k |
| **gemini-2.5-flash** | Google | \$0.10 | \$0.40 | \$0.025 | 1000k |
| **deepseek-v3** | DeepSeek | \$0.14 | \$0.28 | \$0.014 | 64k |
| **deepseek-r1** | DeepSeek | \$0.55 | \$2.19 | \$0.14 | 64k |

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) to see how to add new models, update pricing, or add features.

## 📄 License

TokenTally is open-source software licensed under the [MIT License](LICENSE).
