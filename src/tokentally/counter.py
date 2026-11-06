"""
Fast token counting utilities with support for tiktoken and zero-dependency fallbacks.
"""

import math
import os
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Union

# Try importing tiktoken optionally
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None  # type: ignore
    _TIKTOKEN_AVAILABLE = False


@dataclass(frozen=True)
class TokenCountResult:
    """Detailed tokenization result guaranteeing transparency between exact and heuristic counts."""
    tokens: int
    method: str  # "exact_bpe" or "calibrated_heuristic"
    encoding: str
    is_exact: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Model to tiktoken encoding mapping
MODEL_TO_ENCODING = {
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "o1": "o200k_base",
    "o1-mini": "o200k_base",
    "o3-mini": "o200k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-4": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
}

# Calibrated tokenization regex matching leading space with word/number/punctuation
_TOKEN_PATTERN = re.compile(
    r"""'s|'t|'re|'ve|'m|'ll|'d| ?[a-zA-Z]+| ?\d+| ?[^\s\w]+|\s+"""
)


def get_model_encoding(model_name: str) -> str:
    """Return the tiktoken encoding name suitable for the model."""
    name = model_name.strip().lower()
    if name in MODEL_TO_ENCODING:
        return MODEL_TO_ENCODING[name]
    if name.startswith(("gpt-4o", "o1", "o3", "llama", "deepseek", "qwen", "groq-llama", "cerebras-llama")):
        return "o200k_base"
    return "cl100k_base"


class TokenCounter:
    """
    High-performance token counter.
    Uses tiktoken when available, and falls back to calibrated heuristic tokenization.
    """

    def __init__(self, force_heuristic: bool = False):
        self.force_heuristic = force_heuristic
        self._encoders = {}

    @property
    def has_tiktoken(self) -> bool:
        return _TIKTOKEN_AVAILABLE and not self.force_heuristic

    def _get_encoder(self, encoding_name: str):
        if not self.has_tiktoken:
            return None
        if encoding_name not in self._encoders:
            try:
                self._encoders[encoding_name] = tiktoken.get_encoding(encoding_name)
            except Exception:
                return None
        return self._encoders.get(encoding_name)

    def count_heuristic(self, text: str) -> int:
        """
        Calibrated zero-dependency token count estimation.
        Handles code, English, identifiers, whitespace, and punctuation.
        """
        if not text:
            return 0

        # Fast path for very short strings
        length = len(text)
        if length <= 4:
            return 1

        matches = _TOKEN_PATTERN.findall(text)
        count = 0
        for token in matches:
            t = token.strip()
            t_len = len(t)
            if t_len > 7:
                count += math.ceil(t_len / 4.0)
            elif t_len > 0:
                count += 1
            else:
                # pure whitespace chunk
                count += max(1, len(token) // 4)
        return max(1, count)

    def count_detailed(self, text: str, model: str = "gpt-4o") -> TokenCountResult:
        """
        Count tokens with full methodology transparency (exact BPE vs calibrated heuristic).
        """
        if not text:
            enc_name = get_model_encoding(model)
            return TokenCountResult(tokens=0, method="exact_bpe" if self.has_tiktoken else "calibrated_heuristic", encoding=enc_name, is_exact=self.has_tiktoken)

        enc_name = get_model_encoding(model)
        if self.has_tiktoken:
            encoder = self._get_encoder(enc_name)
            if encoder is not None:
                try:
                    num_tok = len(encoder.encode(text, disallowed_special=()))
                    return TokenCountResult(tokens=num_tok, method="exact_bpe", encoding=enc_name, is_exact=True)
                except Exception:
                    pass

        heuristic_cnt = self.count_heuristic(text)
        return TokenCountResult(tokens=heuristic_cnt, method="calibrated_heuristic", encoding="heuristic_regex", is_exact=False)

    def count(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count the number of tokens in the given text for the specified model.
        """
        return self.count_detailed(text, model=model).tokens

    def count_file_detailed(self, file_path: Union[str, os.PathLike], model: str = "gpt-4o") -> TokenCountResult:
        """Read a file from disk and return detailed token count result."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.count_detailed(content, model=model)

    def count_file(self, file_path: Union[str, os.PathLike], model: str = "gpt-4o") -> int:
        """
        Read a file from disk and return its token count.
        """
        return self.count_file_detailed(file_path, model=model).tokens


# Global default instance
_DEFAULT_COUNTER = TokenCounter()


def count_tokens_detailed(text_or_file: str, model: str = "gpt-4o", is_file: bool = False) -> TokenCountResult:
    """
    Convenience helper function to count tokens with exact vs heuristic transparency.
    """
    if is_file or (os.path.isfile(text_or_file) if len(text_or_file) < 500 else False):
        try:
            return _DEFAULT_COUNTER.count_file_detailed(text_or_file, model=model)
        except OSError:
            pass
    return _DEFAULT_COUNTER.count_detailed(text_or_file, model=model)


def count_tokens(text_or_file: str, model: str = "gpt-4o", is_file: bool = False) -> int:
    """
    Convenience helper function to count tokens in a string or file (returns integer count).
    """
    return count_tokens_detailed(text_or_file, model=model, is_file=is_file).tokens
