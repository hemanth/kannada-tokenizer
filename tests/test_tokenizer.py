"""Tests for the top-level tokenize function."""

from kannada_tokenizer import tokenize


def test_tokenize_basic():
    tokens = tokenize('dharma yōga')
    assert 'ಧರ್ಮ' in tokens
    assert 'ಯೋಗ' in tokens


def test_tokenize_empty():
    assert tokenize('') == []


def test_tokenize_whitespace():
    assert tokenize('   ') == []


def test_tokenize_kannada_input():
    tokens = tokenize('ಧರ್ಮ ಯೋಗ')
    assert 'ಧರ್ಮ' in tokens
    assert 'ಯೋಗ' in tokens
    # tokens should be in Kannada script
    for tok in tokens:
        assert any(0x0C80 <= ord(c) <= 0x0CFF for c in tok), (
            f"Token '{tok}' does not contain Kannada characters"
        )


def test_tokenize_punctuation_danda():
    tokens = tokenize('dharma। yōga')
    assert 'ಧರ್ಮ' in tokens
    assert 'ಯೋಗ' in tokens
