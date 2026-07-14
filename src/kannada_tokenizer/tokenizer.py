"""Main tokenizer module for Kannada text processing.

Mirrors the Sanskrit tokenizer architecture, adapted for Kannada script
(Unicode block U+0C80–U+0CFF) and ISO 15919 transliteration.
"""

from __future__ import annotations

import re

from .transliterate import normalize_to_iso15919
from .sandhi import split_sandhi


# Punctuation pattern: Kannada-specific punctuation, Devanagari dandas,
# common Latin punctuation, and whitespace.
_SPLIT_PATTERN = re.compile(
    r"[\s।॥\.\,\;\:\!\?\"\'\(\)\[\]\{\}\-\—\–]+"
)


def tokenize(text: str) -> list[str]:
    """Tokenize Kannada text with transliteration normalization and sandhi splitting.

    Pipeline:
        1. Normalize input to ISO 15919.
        2. Split on whitespace and punctuation (dandas, periods, commas, etc.).
        3. Attempt sandhi splitting on each word.
        4. Lowercase all tokens and filter empties.

    Args:
        text: Input Kannada text in any supported script/transliteration.

    Returns:
        A flat list of lowercase token strings.
    """
    if not text or not text.strip():
        return []

    normalized: str = normalize_to_iso15919(text)
    raw_words: list[str] = _SPLIT_PATTERN.split(normalized)

    tokens: list[str] = []
    for word in raw_words:
        word = word.strip()
        if not word:
            continue
        # Attempt sandhi splitting; returns a list of sub-tokens
        sub_tokens: list[str] = split_sandhi(word)
        tokens.extend(sub_tokens)

    # Lowercase and final empty filter
    return [t.lower() for t in tokens if t.strip()]


def tokenize_words(text: str) -> list[str]:
    """Tokenize Kannada text at word boundaries only (no sandhi splitting).

    Useful when sandhi analysis is not needed or when working with
    pre-split text.

    Args:
        text: Input Kannada text in any supported script/transliteration.

    Returns:
        A flat list of lowercase word-level tokens.
    """
    if not text or not text.strip():
        return []

    normalized: str = normalize_to_iso15919(text)
    raw_words: list[str] = _SPLIT_PATTERN.split(normalized)

    return [w.lower() for w in raw_words if w.strip()]
