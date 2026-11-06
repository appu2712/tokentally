"""
Model registry and pricing definitions for major LLM providers.
Prices are represented in USD per 1,000,000 tokens.
Supports dynamic local pricing overrides via ~/.tokentally/pricing.json
"""

import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ModelPricing:
    """Pricing specifications for a specific model."""
    provider: str
    name: str
    input_per_m: float
    output_per_m: float
    cached_input_per_m: Optional[float] = None
    context_window: int = 128000
    description: str = ""
    is_local: bool = False
    is_inferred: bool = False
    inference_rationale: Optional[str] = None

    @property
    def has_caching(self) -> bool:
        return self.cached_input_per_m is not None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Built-in canonical registry of leading frontier, open-source, and cloud models (USD per 1M tokens)
_BUILTIN_REGISTRY: Dict[str, ModelPricing] = {
    # OpenAI Frontier & Reasoning
    "gpt-5": ModelPricing(
        provider="OpenAI",
        name="gpt-5",
        input_per_m=15.00,
        output_per_m=60.00,
        cached_input_per_m=7.50,
        context_window=256000,
        description="Next-generation GPT-5 frontier multimodal foundation model",
    ),
    "gpt-luma": ModelPricing(
        provider="OpenAI",
        name="gpt-luma",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="High-throughput multimodal agent model for production scale",
    ),
    "gpt-sol": ModelPricing(
        provider="OpenAI",
        name="gpt-sol",
        input_per_m=0.20,
        output_per_m=0.80,
        cached_input_per_m=0.05,
        context_window=128000,
        description="Ultra-efficient daily reasoning and low-latency task processing model",
    ),
    "gpt-astra": ModelPricing(
        provider="OpenAI",
        name="gpt-astra",
        input_per_m=10.00,
        output_per_m=40.00,
        cached_input_per_m=2.50,
        context_window=256000,
        description="Autonomous agentic reasoning and multi-step tool orchestration model",
    ),
    "o4": ModelPricing(
        provider="OpenAI",
        name="o4",
        input_per_m=10.00,
        output_per_m=40.00,
        cached_input_per_m=5.00,
        context_window=256000,
        description="OpenAI next-generation o4 reasoning architecture",
    ),
    "gpt-4.5": ModelPricing(
        provider="OpenAI",
        name="gpt-4.5",
        input_per_m=75.00,
        output_per_m=150.00,
        cached_input_per_m=37.50,
        context_window=128000,
        description="OpenAI Orion frontier model with world knowledge and deep contextual synthesis",
    ),
    "o3": ModelPricing(
        provider="OpenAI",
        name="o3",
        input_per_m=10.00,
        output_per_m=40.00,
        cached_input_per_m=5.00,
        context_window=200000,
        description="Flagship OpenAI o3 deep reasoning model for competitive programming and research",
    ),
    "o3-pro": ModelPricing(
        provider="OpenAI",
        name="o3-pro",
        input_per_m=20.00,
        output_per_m=80.00,
        cached_input_per_m=10.00,
        context_window=200000,
        description="High-compute o3 model for extended verification and mission-critical logic",
    ),
    "o3-mini": ModelPricing(
        provider="OpenAI",
        name="o3-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=200000,
        description="High-speed reasoning model balancing coding depth and low latency",
    ),
    "o1": ModelPricing(
        provider="OpenAI",
        name="o1",
        input_per_m=15.00,
        output_per_m=60.00,
        cached_input_per_m=7.50,
        context_window=200000,
        description="State of the art deep reasoning model with internal chain of thought",
    ),
    "o1-mini": ModelPricing(
        provider="OpenAI",
        name="o1-mini",
        input_per_m=1.10,
        output_per_m=4.40,
        cached_input_per_m=0.55,
        context_window=128000,
        description="Fast reasoning model optimized for coding, mathematics, and STEM",
    ),
    "gpt-4o": ModelPricing(
        provider="OpenAI",
        name="gpt-4o",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="Flagship multimodal omni model for general intelligence and multimodal coding",
    ),
    "gpt-4o-mini": ModelPricing(
        provider="OpenAI",
        name="gpt-4o-mini",
        input_per_m=0.15,
        output_per_m=0.60,
        cached_input_per_m=0.075,
        context_window=128000,
        description="Fast, cost-efficient small model for high-frequency tasks",
    ),
    "gpt-4-turbo": ModelPricing(
        provider="OpenAI",
        name="gpt-4-turbo",
        input_per_m=10.00,
        output_per_m=30.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Previous generation GPT-4 Turbo model",
    ),
    "gpt-3.5-turbo": ModelPricing(
        provider="OpenAI",
        name="gpt-3.5-turbo",
        input_per_m=0.50,
        output_per_m=1.50,
        cached_input_per_m=None,
        context_window=16385,
        description="Legacy lightweight model",
    ),

    # Anthropic Claude 3.5, 3.7, 3.8 & 4
    "claude-4-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-4-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=300000,
        description="Anthropic Claude 4 Sonnet next-generation flagship coding and agent model",
    ),
    "claude-4-opus": ModelPricing(
        provider="Anthropic",
        name="claude-4-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=300000,
        description="Anthropic Claude 4 Opus frontier compute and deep reasoning architecture",
    ),
    "claude-3-8-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-3-8-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Claude 3.8 Sonnet with adaptive chain-of-thought and agent reasoning",
    ),
    "claude-3-8-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-8-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="Claude 3.8 Opus frontier synthesis and research model",
    ),
    "claude-3-7-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-3-7-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Hybrid standard and extended-thinking frontier coding model",
    ),
    "claude-3-5-sonnet": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="High-intelligence industry standard for autonomous agents and codebases",
    ),
    "claude-3-5-haiku": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-haiku",
        input_per_m=0.80,
        output_per_m=4.00,
        cached_input_per_m=0.08,
        context_window=200000,
        description="Ultra-fast, responsive lightweight model for edge processing",
    ),
    "claude-3-5-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-5-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="Anthropic frontier high-compute model for deep complex architectures",
    ),
    "claude-3-opus": ModelPricing(
        provider="Anthropic",
        name="claude-3-opus",
        input_per_m=15.00,
        output_per_m=75.00,
        cached_input_per_m=1.50,
        context_window=200000,
        description="Deep contextual synthesis and long-form analysis",
    ),

    # Google Gemini 2.0, 2.5, 3.8 & Gemini 4 Argon
    "gemini-4-argon": ModelPricing(
        provider="Google",
        name="gemini-4-argon",
        input_per_m=1.50,
        output_per_m=6.00,
        cached_input_per_m=0.375,
        context_window=2000000,
        description="Google next-generation Gemini 4 Argon architecture with 2M native context",
    ),
    "gemini-4-argon-pro": ModelPricing(
        provider="Google",
        name="gemini-4-argon-pro",
        input_per_m=1.50,
        output_per_m=6.00,
        cached_input_per_m=0.375,
        context_window=2000000,
        description="Gemini 4 Argon Pro frontier multimodal reasoning foundation model",
    ),
    "gemini-4-argon-flash": ModelPricing(
        provider="Google",
        name="gemini-4-argon-flash",
        input_per_m=0.12,
        output_per_m=0.48,
        cached_input_per_m=0.03,
        context_window=2000000,
        description="Gemini 4 Argon Flash high-throughput, low-latency multimodal model",
    ),
    "gemini-4-argon-thinking": ModelPricing(
        provider="Google",
        name="gemini-4-argon-thinking",
        input_per_m=0.35,
        output_per_m=1.40,
        cached_input_per_m=0.0875,
        context_window=2000000,
        description="Gemini 4 Argon with integrated deep reasoning traces",
    ),
    "gemini-3.8": ModelPricing(
        provider="Google",
        name="gemini-3.8",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=2000000,
        description="Gemini 3.8 multimodal foundation model with 2M token context",
    ),
    "gemini-3.8-pro": ModelPricing(
        provider="Google",
        name="gemini-3.8-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=2000000,
        description="Gemini 3.8 Pro multimodal model with 2M context",
    ),
    "gemini-3.8-flash": ModelPricing(
        provider="Google",
        name="gemini-3.8-flash",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=2000000,
        description="Gemini 3.8 Flash high-efficiency workhorse model",
    ),
    "gemini-3.8-live": ModelPricing(
        provider="Google",
        name="gemini-3.8-live",
        input_per_m=0.15,
        output_per_m=0.60,
        cached_input_per_m=0.0375,
        context_window=1000000,
        description="Gemini 3.8 Live low-latency bidirectional streaming voice/video model with async tools",
    ),
    "gemini-3.8-live-extended-thinking": ModelPricing(
        provider="Google",
        name="gemini-3.8-live-extended-thinking",
        input_per_m=0.30,
        output_per_m=1.20,
        cached_input_per_m=0.075,
        context_window=1000000,
        description="Gemini 3.8 Live with continuous background reasoning and conversational pacing",
    ),
    "gemini-3.5-transcribe-live": ModelPricing(
        provider="Google",
        name="gemini-3.5-transcribe-live",
        input_per_m=0.08,
        output_per_m=0.08,
        cached_input_per_m=None,
        context_window=500000,
        description="Gemini 3.5 real-time streaming speech-to-text with interim hypotheses",
    ),
    "gemini-3.5-live-translate-preview": ModelPricing(
        provider="Google",
        name="gemini-3.5-live-translate-preview",
        input_per_m=0.12,
        output_per_m=0.12,
        cached_input_per_m=None,
        context_window=500000,
        description="Gemini 3.5 real-time speech-to-speech translation across 70+ languages",
    ),
    "gemini-2.5-pro": ModelPricing(
        provider="Google",
        name="gemini-2.5-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=1000000,
        description="Advanced reasoning multimodal model with 1M context window",
    ),
    "gemini-2.5-flash": ModelPricing(
        provider="Google",
        name="gemini-2.5-flash",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Cost-optimized high-speed multimodal model",
    ),
    "gemini-2.0-flash-thinking": ModelPricing(
        provider="Google",
        name="gemini-2.0-flash-thinking",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Gemini Flash with integrated reasoning and verifiable thinking traces",
    ),
    "gemini-2.0-flash": ModelPricing(
        provider="Google",
        name="gemini-2.0-flash",
        input_per_m=0.10,
        output_per_m=0.40,
        cached_input_per_m=0.025,
        context_window=1000000,
        description="Real-time multimodal streaming model",
    ),
    "gemini-2.0-pro": ModelPricing(
        provider="Google",
        name="gemini-2.0-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=2000000,
        description="Frontier multimodal Gemini 2.0 Pro model with 2M context window",
    ),
    "gemini-1.5-pro": ModelPricing(
        provider="Google",
        name="gemini-1.5-pro",
        input_per_m=1.25,
        output_per_m=5.00,
        cached_input_per_m=0.3125,
        context_window=2000000,
        description="Ultra-long 2M context window model",
    ),
    "gemini-1.5-flash": ModelPricing(
        provider="Google",
        name="gemini-1.5-flash",
        input_per_m=0.075,
        output_per_m=0.30,
        cached_input_per_m=0.01875,
        context_window=1000000,
        description="Ultra-low cost high-volume model",
    ),

    # xAI Grok
    "grok-3.5": ModelPricing(
        provider="xAI",
        name="grok-3.5",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.75,
        context_window=200000,
        description="xAI next-generation flagship frontier intelligence and coding model",
    ),
    "grok-3.5-mini": ModelPricing(
        provider="xAI",
        name="grok-3.5-mini",
        input_per_m=0.30,
        output_per_m=1.50,
        cached_input_per_m=0.075,
        context_window=200000,
        description="High-speed lightweight reasoning model by xAI",
    ),
    "grok-3-deepsearch": ModelPricing(
        provider="xAI",
        name="grok-3-deepsearch",
        input_per_m=5.00,
        output_per_m=25.00,
        cached_input_per_m=1.25,
        context_window=200000,
        description="xAI autonomous agentic web search and deep research synthesis model",
    ),
    "grok-3": ModelPricing(
        provider="xAI",
        name="grok-3",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.75,
        context_window=131072,
        description="xAI flagship frontier intelligence and coding model",
    ),
    "grok-3-mini": ModelPricing(
        provider="xAI",
        name="grok-3-mini",
        input_per_m=0.30,
        output_per_m=1.50,
        cached_input_per_m=0.075,
        context_window=131072,
        description="High-speed lightweight reasoning model by xAI",
    ),
    "grok-2": ModelPricing(
        provider="xAI",
        name="grok-2",
        input_per_m=2.00,
        output_per_m=10.00,
        cached_input_per_m=0.50,
        context_window=131072,
        description="xAI multimodal general capability model",
    ),
    "grok-2-mini": ModelPricing(
        provider="xAI",
        name="grok-2-mini",
        input_per_m=0.20,
        output_per_m=1.00,
        cached_input_per_m=0.05,
        context_window=131072,
        description="Compact xAI inference model for low-latency queries",
    ),

    # DeepSeek
    "deepseek-v4": ModelPricing(
        provider="DeepSeek",
        name="deepseek-v4",
        input_per_m=0.18,
        output_per_m=0.36,
        cached_input_per_m=0.018,
        context_window=128000,
        description="DeepSeek 4th-generation frontier MoE foundation model",
    ),
    "deepseek-r2": ModelPricing(
        provider="DeepSeek",
        name="deepseek-r2",
        input_per_m=0.65,
        output_per_m=2.40,
        cached_input_per_m=0.16,
        context_window=128000,
        description="DeepSeek 2nd-generation deep reasoning model with verifiable chain-of-thought",
    ),
    "deepseek-coder-v3": ModelPricing(
        provider="DeepSeek",
        name="deepseek-coder-v3",
        input_per_m=0.14,
        output_per_m=0.28,
        cached_input_per_m=0.014,
        context_window=128000,
        description="Specialized high-efficiency code generation and repository synthesis",
    ),
    "deepseek-v3": ModelPricing(
        provider="DeepSeek",
        name="deepseek-v3",
        input_per_m=0.14,
        output_per_m=0.28,
        cached_input_per_m=0.014,
        context_window=64000,
        description="Leading open-architecture frontier MoE model",
    ),
    "deepseek-r1": ModelPricing(
        provider="DeepSeek",
        name="deepseek-r1",
        input_per_m=0.55,
        output_per_m=2.19,
        cached_input_per_m=0.14,
        context_window=64000,
        description="Reinforcement learning reasoning model with verifiable CoT",
    ),

    # Mistral AI
    "mistral-large-3": ModelPricing(
        provider="Mistral",
        name="mistral-large-3",
        input_per_m=2.00,
        output_per_m=6.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Mistral 3rd-generation flagship frontier model for reasoning and coding",
    ),
    "devstral": ModelPricing(
        provider="Mistral",
        name="devstral",
        input_per_m=0.30,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=256000,
        description="Specialized agentic software engineering and repo-level coding model",
    ),
    "ministral-8b": ModelPricing(
        provider="Mistral",
        name="ministral-8b",
        input_per_m=0.10,
        output_per_m=0.10,
        cached_input_per_m=None,
        context_window=128000,
        description="Mistral edge on-device 8B parameter model",
    ),
    "ministral-3b": ModelPricing(
        provider="Mistral",
        name="ministral-3b",
        input_per_m=0.04,
        output_per_m=0.04,
        cached_input_per_m=None,
        context_window=128000,
        description="Ultra-compact 3B edge model for local and low-latency inference",
    ),
    "mistral-saba": ModelPricing(
        provider="Mistral",
        name="mistral-saba",
        input_per_m=0.20,
        output_per_m=0.60,
        cached_input_per_m=None,
        context_window=32768,
        description="High-throughput reasoning model fine-tuned for Middle Eastern and Indic domains",
    ),
    "pixtral-large": ModelPricing(
        provider="Mistral",
        name="pixtral-large",
        input_per_m=2.00,
        output_per_m=6.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Mistral 124B parameter multimodal multimodal reasoning frontier model",
    ),
    "pixtral-12b": ModelPricing(
        provider="Mistral",
        name="pixtral-12b",
        input_per_m=0.15,
        output_per_m=0.15,
        cached_input_per_m=None,
        context_window=128000,
        description="Lightweight multimodal visual inspection model",
    ),
    "codestral-2501": ModelPricing(
        provider="Mistral",
        name="codestral-2501",
        input_per_m=0.30,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=256000,
        description="Latest generation code synthesis and fill-in-the-middle model",
    ),
    "mistral-large": ModelPricing(
        provider="Mistral",
        name="mistral-large",
        input_per_m=2.00,
        output_per_m=6.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Mistral flagship frontier model for reasoning and coding",
    ),
    "codestral": ModelPricing(
        provider="Mistral",
        name="codestral",
        input_per_m=0.30,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=256000,
        description="Specialized code generation and fill-in-the-middle model",
    ),
    "mistral-small": ModelPricing(
        provider="Mistral",
        name="mistral-small",
        input_per_m=0.10,
        output_per_m=0.30,
        cached_input_per_m=None,
        context_window=128000,
        description="Fast low-latency edge model",
    ),

    # Groq / Cerebras Hosted LPUs (Per million tokens)
    "groq-deepseek-r1": ModelPricing(
        provider="Groq",
        name="groq-deepseek-r1",
        input_per_m=0.75,
        output_per_m=0.99,
        cached_input_per_m=None,
        context_window=128000,
        description="Ultra-high throughput LPU hosted DeepSeek R1 reasoning model",
    ),
    "cerebras-deepseek-r1": ModelPricing(
        provider="Cerebras",
        name="cerebras-deepseek-r1",
        input_per_m=0.70,
        output_per_m=0.70,
        cached_input_per_m=None,
        context_window=128000,
        description="Sub-second wafer-scale engine inference for DeepSeek R1",
    ),
    "groq-llama-3.3-70b": ModelPricing(
        provider="Groq",
        name="groq-llama-3.3-70b",
        input_per_m=0.59,
        output_per_m=0.79,
        cached_input_per_m=None,
        context_window=128000,
        description="Ultra-high throughput LPU hosted 70B parameter model",
    ),
    "groq-mixtral-8x7b": ModelPricing(
        provider="Groq",
        name="groq-mixtral-8x7b",
        input_per_m=0.24,
        output_per_m=0.24,
        cached_input_per_m=None,
        context_window=32768,
        description="Fast MoE inference on Groq LPUs",
    ),

    # Cerebras Wafer-Scale Engine
    "cerebras-llama-3.3-70b": ModelPricing(
        provider="Cerebras",
        name="cerebras-llama-3.3-70b",
        input_per_m=0.60,
        output_per_m=0.60,
        cached_input_per_m=None,
        context_window=128000,
        description="Sub-second 70B inference on Cerebras CS-3",
    ),
    "cerebras-llama-3.1-8b": ModelPricing(
        provider="Cerebras",
        name="cerebras-llama-3.1-8b",
        input_per_m=0.10,
        output_per_m=0.10,
        cached_input_per_m=None,
        context_window=128000,
        description="Ultra-low latency 8B inference on Cerebras CS-3",
    ),

    # Cohere
    "command-a": ModelPricing(
        provider="Cohere",
        name="command-a",
        input_per_m=1.50,
        output_per_m=6.00,
        cached_input_per_m=0.375,
        context_window=256000,
        description="Cohere flagship enterprise agentic action and multi-step tool model",
    ),
    "command-r7b": ModelPricing(
        provider="Cohere",
        name="command-r7b",
        input_per_m=0.0375,
        output_per_m=0.15,
        cached_input_per_m=0.01875,
        context_window=128000,
        description="Cohere ultra-efficient multilingual enterprise workhorse model",
    ),
    "command-r": ModelPricing(
        provider="Cohere",
        name="command-r",
        input_per_m=0.15,
        output_per_m=0.60,
        cached_input_per_m=0.075,
        context_window=128000,
        description="Cohere scalable RAG and enterprise tool use model",
    ),
    "command-r-plus": ModelPricing(
        provider="Cohere",
        name="command-r-plus",
        input_per_m=2.50,
        output_per_m=10.00,
        cached_input_per_m=1.25,
        context_window=128000,
        description="Cohere flagship enterprise multi-step reasoning model",
    ),

    # AWS Bedrock
    "bedrock-nova-premier": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-premier",
        input_per_m=2.00,
        output_per_m=8.00,
        cached_input_per_m=0.50,
        context_window=300000,
        description="Amazon Bedrock premier frontier multimodal reasoning model",
    ),
    "bedrock-claude-3-7-sonnet": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-claude-3-7-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Claude 3.7 Sonnet deployed on AWS Bedrock",
    ),
    "bedrock-claude-3-5-sonnet": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-claude-3-5-sonnet",
        input_per_m=3.00,
        output_per_m=15.00,
        cached_input_per_m=0.30,
        context_window=200000,
        description="Anthropic Claude 3.5 Sonnet hosted via Amazon Bedrock",
    ),
    "bedrock-nova-pro": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-pro",
        input_per_m=0.80,
        output_per_m=3.20,
        cached_input_per_m=0.20,
        context_window=300000,
        description="Amazon Nova Pro multimodal reasoning model",
    ),
    "bedrock-nova-lite": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-lite",
        input_per_m=0.06,
        output_per_m=0.24,
        cached_input_per_m=0.015,
        context_window=300000,
        description="Amazon Nova Lite ultra-low cost high-speed model",
    ),
    "bedrock-nova-micro": ModelPricing(
        provider="AWS Bedrock",
        name="bedrock-nova-micro",
        input_per_m=0.035,
        output_per_m=0.14,
        cached_input_per_m=None,
        context_window=128000,
        description="Amazon Nova Micro text-only low latency model",
    ),

    # Alibaba Qwen
    "qwen-3-max": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-3-max",
        input_per_m=1.60,
        output_per_m=6.40,
        cached_input_per_m=None,
        context_window=256000,
        description="Qwen 3rd-generation frontier dense model matching leading benchmarks",
    ),
    "qwen-3-coder-72b": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-3-coder-72b",
        input_per_m=0.35,
        output_per_m=0.40,
        cached_input_per_m=None,
        context_window=256000,
        description="Qwen 3 flagship open coding model with 256k context",
    ),
    "qwen-3-coder-32b": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-3-coder-32b",
        input_per_m=0.20,
        output_per_m=0.20,
        cached_input_per_m=None,
        context_window=256000,
        description="Qwen 3 specialized high-capability code generation model",
    ),
    "qwen-vl-max": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-vl-max",
        input_per_m=1.60,
        output_per_m=6.40,
        cached_input_per_m=None,
        context_window=128000,
        description="Qwen flagship vision-language multimodal foundation model",
    ),
    "qwen-2.5-max": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-2.5-max",
        input_per_m=1.60,
        output_per_m=6.40,
        cached_input_per_m=None,
        context_window=128000,
        description="Qwen flagship frontier dense model matching frontier benchmarks",
    ),
    "qwen-2.5-coder-32b": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-2.5-coder-32b",
        input_per_m=0.20,
        output_per_m=0.20,
        cached_input_per_m=None,
        context_window=128000,
        description="Specialized high-capability open coding model",
    ),
    "qwen-2.5-72b": ModelPricing(
        provider="Alibaba / Open",
        name="qwen-2.5-72b",
        input_per_m=0.35,
        output_per_m=0.40,
        cached_input_per_m=None,
        context_window=128000,
        description="General open-weights flagship multilingual model",
    ),

    # Meta LLaMA 4, 3.3, 3.2, 3.1
    "llama-4-behemoth": ModelPricing(
        provider="Meta / Open",
        name="llama-4-behemoth",
        input_per_m=2.00,
        output_per_m=2.00,
        cached_input_per_m=None,
        context_window=256000,
        description="Meta LLaMA 4 400B+ open frontier foundation architecture",
    ),
    "llama-4-maverick": ModelPricing(
        provider="Meta / Open",
        name="llama-4-maverick",
        input_per_m=0.70,
        output_per_m=0.80,
        cached_input_per_m=None,
        context_window=256000,
        description="Meta LLaMA 4 flagship open weights frontier coding and reasoning model",
    ),
    "llama-4-scout": ModelPricing(
        provider="Meta / Open",
        name="llama-4-scout",
        input_per_m=0.15,
        output_per_m=0.15,
        cached_input_per_m=None,
        context_window=128000,
        description="Meta LLaMA 4 high-speed multimodal vision-language model",
    ),
    "llama-3.3-70b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.3-70b",
        input_per_m=0.70,
        output_per_m=0.80,
        cached_input_per_m=None,
        context_window=128000,
        description="Flagship open weights 70B model",
    ),
    "llama-3.2-90b-vision": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-90b-vision",
        input_per_m=0.90,
        output_per_m=0.90,
        cached_input_per_m=None,
        context_window=128000,
        description="Meta vision multimodal flagship 90B model",
    ),
    "llama-3.2-11b-vision": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-11b-vision",
        input_per_m=0.16,
        output_per_m=0.16,
        cached_input_per_m=None,
        context_window=128000,
        description="Meta lightweight vision multimodal 11B model",
    ),
    "llama-3.2-3b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-3b",
        input_per_m=0.04,
        output_per_m=0.04,
        cached_input_per_m=None,
        context_window=128000,
        description="Edge and on-device compact 3B model",
    ),
    "llama-3.2-1b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.2-1b",
        input_per_m=0.02,
        output_per_m=0.02,
        cached_input_per_m=None,
        context_window=128000,
        description="Micro-instance 1B model for high-throughput classification",
    ),
    "llama-3.1-405b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.1-405b",
        input_per_m=2.50,
        output_per_m=2.50,
        cached_input_per_m=None,
        context_window=128000,
        description="Frontier scale open weights 405B model",
    ),
    "llama-3.1-8b": ModelPricing(
        provider="Meta / Open",
        name="llama-3.1-8b",
        input_per_m=0.05,
        output_per_m=0.05,
        cached_input_per_m=None,
        context_window=128000,
        description="Lightweight 8B open model for local or micro-instance deployment",
    ),

    # Microsoft Phi Family
    "phi-4": ModelPricing(
        provider="Microsoft",
        name="phi-4",
        input_per_m=0.07,
        output_per_m=0.14,
        cached_input_per_m=None,
        context_window=128000,
        description="Microsoft Phi-4 14B state-of-the-art small language model with synthetic data reasoning",
    ),
    "phi-4-mini": ModelPricing(
        provider="Microsoft",
        name="phi-4-mini",
        input_per_m=0.03,
        output_per_m=0.06,
        cached_input_per_m=None,
        context_window=128000,
        description="Microsoft Phi-4 Mini 3.8B ultra-fast lightweight model",
    ),
    "phi-4-multimodal": ModelPricing(
        provider="Microsoft",
        name="phi-4-multimodal",
        input_per_m=0.10,
        output_per_m=0.20,
        cached_input_per_m=None,
        context_window=128000,
        description="Microsoft Phi-4 multimodal vision and speech foundation model",
    ),

    # Apple (Apple Intelligence & Private Cloud Compute)
    "apple-pcc-server": ModelPricing(
        provider="Apple",
        name="apple-pcc-server",
        input_per_m=0.25,
        output_per_m=1.00,
        cached_input_per_m=None,
        context_window=128000,
        description="Apple Private Cloud Compute foundation model hosted on Apple silicon servers",
    ),
    "apple-intelligence-local": ModelPricing(
        provider="Apple",
        name="apple-intelligence-local",
        input_per_m=0.00,
        output_per_m=0.00,
        cached_input_per_m=0.00,
        context_window=128000,
        description="Apple on-device AFM 3B model (zero per-token API cost)",
        is_local=True,
    ),

    # Baidu Ernie
    "ernie-4.0-turbo": ModelPricing(
        provider="Baidu",
        name="ernie-4.0-turbo",
        input_per_m=0.40,
        output_per_m=1.20,
        cached_input_per_m=None,
        context_window=128000,
        description="Baidu Ernie 4.0 Turbo enterprise multilingual and Chinese foundation model",
    ),

    # TII Falcon
    "falcon-3-40b": ModelPricing(
        provider="TII Falcon / Open",
        name="falcon-3-40b",
        input_per_m=0.30,
        output_per_m=0.30,
        cached_input_per_m=None,
        context_window=128000,
        description="TII Falcon 3 40B open weights frontier foundation model",
    ),
    "falcon-3-10b": ModelPricing(
        provider="TII Falcon / Open",
        name="falcon-3-10b",
        input_per_m=0.08,
        output_per_m=0.08,
        cached_input_per_m=None,
        context_window=128000,
        description="TII Falcon 3 10B high-efficiency open model",
    ),

    # Ollama / Local Models (Zero dollar inference cost)
    "ollama-local": ModelPricing(
        provider="Ollama (Local)",
        name="ollama-local",
        input_per_m=0.00,
        output_per_m=0.00,
        cached_input_per_m=0.00,
        context_window=128000,
        description="Local on-device inference via Ollama / llama.cpp",
        is_local=True,
    ),
    "vllm-local": ModelPricing(
        provider="vLLM (Self-Hosted)",
        name="vllm-local",
        input_per_m=0.00,
        output_per_m=0.00,
        cached_input_per_m=0.00,
        context_window=128000,
        description="Self-hosted PagedAttention inference server with zero per-token API charges",
        is_local=True,
    ),
}

# User aliases for fast shorthand CLI typing
MODEL_ALIASES = {
    "5": "gpt-5",
    "gpt5": "gpt-5",
    "luma": "gpt-luma",
    "sol": "gpt-sol",
    "astra": "gpt-astra",
    "o4": "o4",
    "4.5": "gpt-4.5",
    "4o": "gpt-4o",
    "4o-mini": "gpt-4o-mini",
    "o1-preview": "o1",
    "o3": "o3",
    "o3m": "o3-mini",
    "o3-mini": "o3-mini",
    "o3-full": "o3",
    "sonnet-4": "claude-4-sonnet",
    "opus-4": "claude-4-opus",
    "sonnet-3.8": "claude-3-8-sonnet",
    "opus-3.8": "claude-3-8-opus",
    "sonnet": "claude-3-7-sonnet",
    "sonnet-3.7": "claude-3-7-sonnet",
    "sonnet-3.5": "claude-3-5-sonnet",
    "haiku": "claude-3-5-haiku",
    "opus": "claude-3-5-opus",
    "argon": "gemini-4-argon",
    "argon-pro": "gemini-4-argon-pro",
    "argon-flash": "gemini-4-argon-flash",
    "argon-thinking": "gemini-4-argon-thinking",
    "gemini-4": "gemini-4-argon",
    "gemini-3.8": "gemini-3.8",
    "gemini-3.8-flash": "gemini-3.8-flash",
    "gemini-live": "gemini-3.8-live",
    "gemini-live-thinking": "gemini-3.8-live-extended-thinking",
    "flash": "gemini-2.5-flash",
    "gemini-flash": "gemini-2.5-flash",
    "gemini-pro": "gemini-2.5-pro",
    "thinking": "gemini-2.0-flash-thinking",
    "grok": "grok-3",
    "grok-mini": "grok-3-mini",
    "deepseek": "deepseek-v3",
    "r1": "deepseek-r1",
    "deepseek-4": "deepseek-v4",
    "v4": "deepseek-v4",
    "r2": "deepseek-r2",
    "deepseek-r2": "deepseek-r2",
    "grok-3.5": "grok-3.5",
    "grok3.5": "grok-3.5",
    "deepsearch": "grok-3-deepsearch",
    "devstral": "devstral",
    "mistral": "mistral-large-3",
    "saba": "mistral-saba",
    "llama-4": "llama-4-maverick",
    "llama4": "llama-4-maverick",
    "maverick": "llama-4-maverick",
    "behemoth": "llama-4-behemoth",
    "scout": "llama-4-scout",
    "phi-4": "phi-4",
    "phi4": "phi-4",
    "phi": "phi-4",
    "ernie": "ernie-4.0-turbo",
    "falcon": "falcon-3-40b",
    "command-a": "command-a",
    "nova-premier": "bedrock-nova-premier",
    "apple": "apple-pcc-server",
    "qwen-3": "qwen-3-max",
    "qwen3": "qwen-3-max",
    "cohere": "command-r",
    "command": "command-r",
    "qwen": "qwen-2.5-coder-32b",
    "qwen-max": "qwen-2.5-max",
    "cerebras": "cerebras-llama-3.3-70b",
    "groq": "groq-llama-3.3-70b",
    "nova": "bedrock-nova-pro",
    "bedrock": "bedrock-claude-3-7-sonnet",
    "local": "ollama-local",
    "ollama": "ollama-local",
    "vllm": "vllm-local",
}


def sync_live_models(source_url: Optional[str] = None, timeout: float = 10.0) -> int:
    """
    Synchronize live pricing and context windows for thousands of frontier and open-source models
    from the global open pricing registry.
    Saves to ~/.tokentally/community_pricing.json.
    Returns the count of successfully synchronized models.
    """
    url = source_url or "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"
    import urllib.request
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "tokentally-cli"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content = resp.read().decode("utf-8")
        data = json.loads(content)

    parsed: Dict[str, Any] = {}
    for k, v in data.items():
        if not isinstance(v, dict) or k == "sample_spec":
            continue
        in_cost = v.get("input_cost_per_token")
        out_cost = v.get("output_cost_per_token")
        if in_cost is None or out_cost is None:
            continue
        in_m = round(float(in_cost) * 1_000_000, 4)
        out_m = round(float(out_cost) * 1_000_000, 4)
        cached_m = round(float(v["cache_read_input_token_cost"]) * 1_000_000, 4) if v.get("cache_read_input_token_cost") is not None else None
        ctx = int(v.get("max_input_tokens") or v.get("max_tokens") or 128000)
        provider = v.get("litellm_provider") or "Community"

        parsed[k.lower()] = {
            "provider": provider.capitalize() if isinstance(provider, str) else "Community",
            "name": k.lower(),
            "input_per_m": in_m,
            "output_per_m": out_m,
            "cached_input_per_m": cached_m,
            "context_window": ctx,
            "description": f"Live synced model ({provider})",
        }

    cfg_dir = Path.home() / ".tokentally"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cfg_dir / "community_pricing.json"
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)

    # Refresh in-memory registry
    global MODEL_REGISTRY
    MODEL_REGISTRY = get_full_registry()
    return len(parsed)


def _load_user_custom_pricing() -> Dict[str, ModelPricing]:
    """Load community synchronized models, local user pricing, and tokentally.toml overrides."""
    custom: Dict[str, ModelPricing] = {}
    cfg_dir = Path.home() / ".tokentally"

    # 1. Load community cached pricing if available
    comm_file = cfg_dir / "community_pricing.json"
    if comm_file.is_file():
        try:
            with open(comm_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    cached_val = val.get("cached_input_per_m")
                    custom[key] = ModelPricing(
                        provider=val.get("provider", "Community"),
                        name=key,
                        input_per_m=float(val.get("input_per_m", 0.0)),
                        output_per_m=float(val.get("output_per_m", 0.0)),
                        cached_input_per_m=float(cached_val) if cached_val is not None else None,
                        context_window=int(val.get("context_window", 128000)),
                        description=val.get("description", "Community registry"),
                    )
        except Exception:
            pass

    # 2. Load manual overrides from ~/.tokentally/pricing.json
    cfg_file = cfg_dir / "pricing.json"
    if cfg_file.is_file():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, val in data.items():
                    cached_val = val.get("cached_input_per_m")
                    custom[key] = ModelPricing(
                        provider=val.get("provider", "Custom"),
                        name=key,
                        input_per_m=float(val.get("input_per_m", 0.0)),
                        output_per_m=float(val.get("output_per_m", 0.0)),
                        cached_input_per_m=float(cached_val) if cached_val is not None else None,
                        context_window=int(val.get("context_window", 128000)),
                        description=val.get("description", "Custom user pricing definition"),
                    )
        except Exception:
            pass

    # 3. Load from local repository tokentally.toml if present
    try:
        from .config import load_config
        cfg = load_config()
        if cfg.custom_models:
            for key, val in cfg.custom_models.items():
                cached_val = val.get("cached_input_per_m")
                custom[key] = ModelPricing(
                    provider=val.get("provider", "Local Config"),
                    name=key,
                    input_per_m=float(val.get("input_per_m", 0.0)),
                    output_per_m=float(val.get("output_per_m", 0.0)),
                    cached_input_per_m=float(cached_val) if cached_val is not None else None,
                    context_window=int(val.get("context_window", 128000)),
                    description=val.get("description", "Declared in tokentally.toml"),
                )
    except Exception:
        pass

    return custom


def save_custom_model(pricing: ModelPricing) -> None:
    """Save or update a custom model pricing in ~/.tokentally/pricing.json."""
    cfg_dir = Path.home() / ".tokentally"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = cfg_dir / "pricing.json"
    data: Dict[str, Any] = {}
    if cfg_file.is_file():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

    data[pricing.name] = {
        "provider": pricing.provider,
        "input_per_m": pricing.input_per_m,
        "output_per_m": pricing.output_per_m,
        "cached_input_per_m": pricing.cached_input_per_m,
        "context_window": pricing.context_window,
        "description": pricing.description,
    }

    with open(cfg_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    # Refresh global registry
    global MODEL_REGISTRY
    MODEL_REGISTRY = get_full_registry()


def remove_custom_model(name: str) -> bool:
    """Remove a custom model definition from ~/.tokentally/pricing.json."""
    cfg_dir = Path.home() / ".tokentally"
    cfg_file = cfg_dir / "pricing.json"
    if not cfg_file.is_file():
        return False

    try:
        with open(cfg_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if name in data:
            del data[name]
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            global MODEL_REGISTRY
            MODEL_REGISTRY = get_full_registry()
            return True
    except Exception:
        pass
    return False


def get_full_registry() -> Dict[str, ModelPricing]:
    """Combine built-in registry with user-defined overrides and live sync cache."""
    reg = dict(_BUILTIN_REGISTRY)
    reg.update(_load_user_custom_pricing())
    return reg


MODEL_REGISTRY = get_full_registry()


def normalize_model_name(name: str) -> str:
    """
    Intelligently normalize user-entered model names, resolving aliases,
    stripping repository/organization prefixes (e.g. 'openai/gpt-4.5' -> 'gpt-4.5'),
    and stripping revision dates or release tags (e.g. 'claude-3-7-sonnet-20250219' -> 'claude-3-7-sonnet').
    """
    if not name:
        return "gpt-4o"
    cleaned = name.strip().lower()

    # Exact canonical match takes precedence over aliases
    reg = get_full_registry()
    if cleaned in reg:
        return cleaned

    # Direct alias match
    if cleaned in MODEL_ALIASES:
        return MODEL_ALIASES[cleaned]

    # Strip provider prefix: "openai/gpt-4o" -> "gpt-4o"
    if "/" in cleaned:
        unprefixed = cleaned.split("/")[-1]
        if unprefixed in MODEL_ALIASES:
            return MODEL_ALIASES[unprefixed]
        if unprefixed in reg:
            return unprefixed
        cleaned = unprefixed

    # Strip version date patterns, e.g. -20241022, -2025-02-19, -001, -latest
    stripped = re.sub(r"-\d{4}-?\d{2}-?\d{2}$", "", cleaned)
    stripped = re.sub(r"-(latest|preview|exp|001|002|instruct)$", "", stripped)

    if stripped in MODEL_ALIASES:
        return MODEL_ALIASES[stripped]
    if stripped in reg:
        return stripped

    # Substring prefix matching for canonical families
    for key in reg:
        if cleaned.startswith(key):
            return key

    return cleaned


def infer_model_pricing(model_name: str) -> Optional[ModelPricing]:
    """
    Heuristically infer pricing and context specifications for newly released or unlisted models
    based on vendor conventions and capability tiers.
    Ensures Tokentally never crashes on future frontier releases.
    Explicitly flags the result with is_inferred=True.
    """
    cleaned = model_name.strip().lower()
    if not cleaned:
        return None

    # Detect provider
    provider = "Generic Provider"
    if any(k in cleaned for k in ("gemini", "argon")):
        provider = "Google"
    elif any(k in cleaned for k in ("claude", "anthropic")):
        provider = "Anthropic"
    elif any(k in cleaned for k in ("gpt", "openai", "luma", "sol", "astra")) or re.match(r"^o\d+", cleaned):
        provider = "OpenAI"
    elif "grok" in cleaned or "xai" in cleaned:
        provider = "xAI"
    elif "deepseek" in cleaned:
        provider = "DeepSeek"
    elif any(k in cleaned for k in ("mistral", "pixtral", "codestral", "saba")):
        provider = "Mistral"
    elif "llama" in cleaned or "meta" in cleaned:
        provider = "Meta / Open"
    elif "qwen" in cleaned:
        provider = "Alibaba / Open"
    elif "cohere" in cleaned or "command" in cleaned:
        provider = "Cohere"
    elif "bedrock" in cleaned or "nova" in cleaned:
        provider = "AWS Bedrock"
    elif "phi" in cleaned or "microsoft" in cleaned:
        provider = "Microsoft"
    elif "apple" in cleaned:
        provider = "Apple"
    elif "ernie" in cleaned or "baidu" in cleaned:
        provider = "Baidu"
    elif "falcon" in cleaned or "tii" in cleaned:
        provider = "TII Falcon / Open"

    # If provider is completely unrecognized, only infer if there is an explicit AI/LLM keyword
    if provider == "Generic Provider":
        has_llm_signal = any(s in cleaned for s in ("llm", "ai-model", "foundation", "instruct", "chat"))
        if not has_llm_signal:
            return None

    # Tokenize name to avoid substring collisions (e.g. 'mini' inside 'gemini')
    tokens = set(re.split(r"[-_./ ]+", cleaned))

    # Detect tier: edge/flash vs high-compute/reasoning vs workhorse
    is_edge = any(t in tokens for t in ("flash", "mini", "nano", "lite", "small", "sol", "haiku", "micro", "8b", "7b", "3b", "1b"))
    is_reasoning = any(t in tokens for t in ("opus", "astra", "ultra", "reasoning", "thinking", "r1", "405b", "orion", "o3-pro", "o4")) or "thinking" in cleaned

    if is_edge:
        tier_label = "Edge / Low-Latency Tier"
        if provider == "Google":
            in_cost, out_cost, cached, ctx = 0.10, 0.40, 0.025, 2000000
        elif provider == "OpenAI":
            in_cost, out_cost, cached, ctx = 0.15, 0.60, 0.075, 128000
        elif provider == "Anthropic":
            in_cost, out_cost, cached, ctx = 0.80, 4.00, 0.08, 200000
        elif provider == "xAI":
            in_cost, out_cost, cached, ctx = 0.30, 1.50, 0.075, 131072
        elif provider == "Meta / Open":
            in_cost, out_cost, cached, ctx = 0.05, 0.05, None, 128000
        elif provider == "Microsoft":
            in_cost, out_cost, cached, ctx = 0.03, 0.06, None, 128000
        elif provider == "Apple":
            in_cost, out_cost, cached, ctx = 0.00, 0.00, 0.00, 128000
        else:
            in_cost, out_cost, cached, ctx = 0.15, 0.60, 0.05, 128000
    elif is_reasoning:
        tier_label = "Frontier High-Compute / Reasoning Tier"
        if provider == "Google":
            in_cost, out_cost, cached, ctx = 0.35, 1.40, 0.0875, 2000000
        elif provider == "OpenAI":
            in_cost, out_cost, cached, ctx = 10.00, 40.00, 5.00, 256000
        elif provider == "Anthropic":
            in_cost, out_cost, cached, ctx = 15.00, 75.00, 1.50, 300000
        elif provider == "DeepSeek":
            in_cost, out_cost, cached, ctx = 0.55, 2.19, 0.14, 64000
        elif provider == "Meta / Open":
            in_cost, out_cost, cached, ctx = 2.50, 2.50, None, 128000
        else:
            in_cost, out_cost, cached, ctx = 10.00, 40.00, 5.00, 200000
    else:
        tier_label = "Workhorse / Flagship Tier"
        if provider == "Google":
            in_cost, out_cost, cached, ctx = 1.25, 5.00, 0.3125, 2000000
        elif provider == "OpenAI":
            in_cost, out_cost, cached, ctx = 2.50, 10.00, 1.25, 128000
        elif provider == "Anthropic":
            in_cost, out_cost, cached, ctx = 3.00, 15.00, 0.30, 300000
        elif provider == "DeepSeek":
            in_cost, out_cost, cached, ctx = 0.14, 0.28, 0.014, 64000
        elif provider == "Meta / Open":
            in_cost, out_cost, cached, ctx = 0.70, 0.80, None, 128000
        elif provider == "Microsoft":
            in_cost, out_cost, cached, ctx = 0.07, 0.14, None, 128000
        elif provider == "Apple":
            in_cost, out_cost, cached, ctx = 0.25, 1.00, None, 128000
        elif provider == "Baidu":
            in_cost, out_cost, cached, ctx = 0.40, 1.20, None, 128000
        elif provider == "TII Falcon / Open":
            in_cost, out_cost, cached, ctx = 0.30, 0.30, None, 128000
        else:
            in_cost, out_cost, cached, ctx = 2.00, 8.00, 1.00, 128000

    rationale = (
        f"Inferred based on {provider} {tier_label} specifications. "
        "Run 'tokentally models --sync' to pull official rates, or override with 'tokentally models --add'."
    )
    return ModelPricing(
        provider=f"{provider} (Inferred)",
        name=cleaned,
        input_per_m=in_cost,
        output_per_m=out_cost,
        cached_input_per_m=cached,
        context_window=ctx,
        description=f"Heuristic tier estimate for uncataloged model '{cleaned}'",
        is_inferred=True,
        inference_rationale=rationale,
    )


def get_model_pricing(name: str, allow_inferred: bool = True) -> ModelPricing:
    """Retrieve pricing specs for a given model or alias. Gracefully infers unlisted frontier models when allow_inferred=True."""
    norm = normalize_model_name(name)
    reg = get_full_registry()
    if norm in reg:
        return reg[norm]

    if allow_inferred:
        inferred = infer_model_pricing(norm)
        if inferred is not None:
            return inferred

    raise KeyError(
        f"Unknown model: '{name}'. Run 'tokentally models --sync' to update the registry, or use 'tokentally models --search <name>' to find matching IDs."
    )


def list_supported_models(
    search: Optional[str] = None,
    provider: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[str]:
    """Return sorted list of supported canonical model identifiers matching search or provider filters."""
    reg = get_full_registry()
    keys = list(reg.keys())

    if search:
        s = search.strip().lower()
        keys = [k for k in keys if s in k.lower() or s in reg[k].description.lower()]

    if provider:
        p = provider.strip().lower()
        keys = [k for k in keys if p in reg[k].provider.lower()]

    keys.sort()
    if limit is not None and limit > 0:
        return keys[:limit]
    return keys
