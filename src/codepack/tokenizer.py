"""
Tokenizer module for CodePack: Estimates token counts for code and prompts.
"""

from typing import Optional

_TIKTOKEN_ENCODER = None
_TIKTOKEN_CHECKED = False


def _get_tiktoken_encoder():
    global _TIKTOKEN_ENCODER, _TIKTOKEN_CHECKED
    if not _TIKTOKEN_CHECKED:
        try:
            import tiktoken
            _TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")
        except Exception:
            _TIKTOKEN_ENCODER = None
        _TIKTOKEN_CHECKED = True
    return _TIKTOKEN_ENCODER


def estimate_tokens(text: str) -> int:
    """
    Estimates the number of tokens in the given text.
    Uses tiktoken cl100k_base if available; falls back to an accurate code heuristic.
    """
    if not text:
        return 0

    encoder = _get_tiktoken_encoder()
    if encoder is not None:
        try:
            return len(encoder.encode(text, disallowed_special=()))
        except Exception:
            pass

    # Heuristic for code & natural language:
    # 1 token is ~3.7-4 characters on average in mixed code and whitespace
    char_count = len(text)
    heuristic_tokens = max(1, int(round(char_count / 3.7)))
    return heuristic_tokens


def format_token_count(count: int) -> str:
    """Formats a token count into a readable string (e.g., '1.2k', '245k')."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}k"
    return str(count)


def format_size(bytes_count: int) -> str:
    """Formats bytes count into a human-readable string (e.g. '14.2 KB')."""
    if bytes_count >= 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.1f} MB"
    elif bytes_count >= 1024:
        return f"{bytes_count / 1024:.1f} KB"
    return f"{bytes_count} B"
