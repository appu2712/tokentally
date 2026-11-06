"""
Fast token counting utilities with support for tiktoken and zero-dependency fallbacks.
"""

import math
import os
import re
from typing import Optional, Union

# Try importing tiktoken optionally
try:
    import tiktoken
    _TIKTOKEN_AVAILABLE = True
except ImportError:
    tiktoken = None  # type: ignore
    _TIKTOKEN_AVAILABLE = False


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
    return MODEL_TO_ENCODING.get(name, "cl100k_base")


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

    def count(self, text: str, model: str = "gpt-4o") -> int:
        """
        Count the number of tokens in the given text for the specified model.
        """
        if not text:
            return 0

        if self.has_tiktoken:
            enc_name = get_model_encoding(model)
            encoder = self._get_encoder(enc_name)
            if encoder is not None:
                try:
                    return len(encoder.encode(text, disallowed_special=()))
                except Exception:
                    pass

        return self.count_heuristic(text)

    def count_file(self, file_path: Union[str, os.PathLike], model: str = "gpt-4o") -> int:
        """
        Read a file from disk and return its token count.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.count(content, model=model)


# Global default instance
_DEFAULT_COUNTER = TokenCounter()


def count_tokens(text_or_file: str, model: str = "gpt-4o", is_file: bool = False) -> int:
    """
    Convenience helper function to count tokens in a string or file.
    """
    if is_file or (os.path.isfile(text_or_file) if len(text_or_file) < 500 else False):
        try:
            return _DEFAULT_COUNTER.count_file(text_or_file, model=model)
        except OSError:
            pass
    return _DEFAULT_COUNTER.count(text_or_file, model=model)
