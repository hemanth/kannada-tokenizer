"""Tests for the top-level tokenize function."""

from kannada_tokenizer import tokenize


def test_tokenize_basic():
    tokens = tokenize('dharma yōga')
    assert 'dharma' in tokens
    assert 'yōga' in tokens


def test_tokenize_empty():
    assert tokenize('') == []


def test_tokenize_whitespace():
    assert tokenize('   ') == []


def test_tokenize_kannada_input():
    tokens = tokenize('ಧರ್ಮ ಯೋಗ')
    assert len(tokens) >= 2
    # tokens should be in ISO 15919, not Kannada script
    for tok in tokens:
        assert all(ord(c) < 0x0C80 or ord(c) > 0x0CFF for c in tok), (
            f"Token '{tok}' still contains Kannada characters"
        )


def test_tokenize_punctuation_danda():
    tokens = tokenize('dharma। yōga')
    assert 'dharma' in tokens
    assert 'yōga' in tokens
