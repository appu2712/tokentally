"""
Native Model Context Protocol (MCP) server implementation for TokenTally.
Allows any MCP-compliant AI assistant (Cursor, Claude Desktop, Antigravity)
to query token counts, model pricing, prompt context decomposition, git review value,
and tool schema footprints.
"""

import json
import sys
from typing import Any, Dict, List, Optional

from .counter import count_tokens_detailed
from .calculator import estimate_cost, compare_models
from .packer import pack_repository
from .optimizer import optimize_prompt
from .analyzer import analyze_prompt_context
from .git import profile_git_diff
from .regression import compare_prompt_regression
from .tools import analyze_tool_schemas, simulate_history_growth


TOOLS_METADATA = [
    {
        "name": "tokentally_estimate_cost",
        "description": "Calculate exact inference dollar cost for a prompt across OpenAI, Anthropic, Gemini, or DeepSeek models.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The text prompt to evaluate"},
                "model": {"type": "string", "default": "gpt-4o", "description": "Target model identifier (e.g. gpt-4o, o1, o3-mini, claude-3-5-sonnet)"},
                "completion_tokens": {"type": "integer", "default": 0, "description": "Expected output completion tokens"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "tokentally_compare_models",
        "description": "Compare dollar cost of a prompt side-by-side across all leading LLMs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The text prompt to evaluate"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "tokentally_analyze_context",
        "description": "Decompose prompt into layers (system instructions, user request, history, tools, RAG) and audit prompt caching potential.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Raw prompt text or chat messages JSON"},
                "model": {"type": "string", "default": "gpt-4o"}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "tokentally_profile_git_diff",
        "description": "Calculate token size and review cost of git changes, classifying lockfiles and generated code to measure Review Value Density.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ref": {"type": "string", "description": "Git branch or commit ref to diff against"},
                "staged": {"type": "boolean", "default": False},
                "exclude_generated": {"type": "boolean", "default": True, "description": "Exclude lockfiles and compiled assets"}
            }
        }
    },
    {
        "name": "tokentally_inspect_tools",
        "description": "Measure token footprint and field complexity of OpenAI / JSON-Schema tool definitions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tools_json": {"type": "string", "description": "JSON string of tool definitions array"}
            },
            "required": ["tools_json"]
        }
    },
    {
        "name": "tokentally_check_regression",
        "description": "Compare candidate prompt against baseline to detect token growth and monthly billing impact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "baseline": {"type": "string", "description": "Baseline prompt text or path"},
                "candidate": {"type": "string", "description": "Candidate prompt text or path"},
                "max_regression_pct": {"type": "number", "default": 15.0}
            },
            "required": ["baseline", "candidate"]
        }
    },
    {
        "name": "tokentally_pack_workspace",
        "description": "Scan a directory and package its source files into an LLM-ready prompt with token breakdown.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Local workspace folder path"},
                "model": {"type": "string", "default": "gpt-4o"},
                "max_tokens": {"type": "integer", "description": "Optional maximum token budget limit"}
            },
            "required": ["directory"]
        }
    },
    {
        "name": "tokentally_optimize_prompt",
        "description": "Minify a prompt by collapsing redundant whitespace and comments while preserving critical instructions and constraints.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The prompt text to optimize"},
                "strip_comments": {"type": "boolean", "default": False}
            },
            "required": ["prompt"]
        }
    }
]


class MCPServer:
    """Stdio JSON-RPC 2.0 MCP server."""

    def __init__(self):
        pass

    def run_stdio(self) -> None:
        """Read JSON-RPC requests from stdin and write responses to stdout."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                res = self.handle_request(req)
                if res is not None:
                    sys.stdout.write(json.dumps(res) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_res = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32603, "message": str(e)}
                }
                sys.stdout.write(json.dumps(err_res) + "\n")
                sys.stdout.flush()

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = req.get("method")
        msg_id = req.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "tokentally-mcp", "version": "0.1.0"}
                }
            }

        elif method == "notifications/initialized":
            return None

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS_METADATA}
            }

        elif method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})

            try:
                out = self.dispatch_tool(name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(out, indent=2)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Error: {e}"}],
                        "isError": True
                    }
                }

        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

    def dispatch_tool(self, name: str, args: Dict[str, Any]) -> Any:
        if name == "tokentally_estimate_cost":
            prompt = args["prompt"]
            model = args.get("model", "gpt-4o")
            comp = args.get("completion_tokens", 0)
            res = estimate_cost(prompt, model=model, completion_tokens=comp)
            return res.to_dict()

        elif name == "tokentally_compare_models":
            prompt = args["prompt"]
            rows = compare_models(prompt)
            return [r.to_dict() for r in rows]

        elif name == "tokentally_analyze_context":
            prompt = args["prompt"]
            model = args.get("model", "gpt-4o")
            res = analyze_prompt_context(prompt, model=model)
            return res.to_dict()

        elif name == "tokentally_profile_git_diff":
            ref = args.get("ref")
            staged = args.get("staged", False)
            exclude_gen = args.get("exclude_generated", True)
            res = profile_git_diff(ref=ref, staged=staged, exclude_generated=exclude_gen)
            return res.to_dict()

        elif name == "tokentally_inspect_tools":
            tools_json = args["tools_json"]
            res = analyze_tool_schemas(tools_json)
            return res.to_dict()

        elif name == "tokentally_check_regression":
            base = args["baseline"]
            cand = args["candidate"]
            max_pct = args.get("max_regression_pct", 15.0)
            res = compare_prompt_regression(base, cand, max_regression_pct=max_pct)
            return res.to_dict()

        elif name == "tokentally_pack_workspace":
            directory = args["directory"]
            model = args.get("model", "gpt-4o")
            max_tok = args.get("max_tokens")
            res = pack_repository(directory, model=model, max_tokens=max_tok)
            return res.to_dict()

        elif name == "tokentally_optimize_prompt":
            prompt = args["prompt"]
            strip_c = args.get("strip_comments", False)
            res = optimize_prompt(prompt, strip_comments=strip_c)
            return res.to_dict()

        raise ValueError(f"Unknown tool: {name}")
