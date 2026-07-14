"""Tests for the transliterate module."""

from kannada_tokenizer.transliterate import (
    kannada_to_iso15919,
    iso15919_to_kannada,
    is_kannada,
    normalize_to_iso15919,
)


# --- kannada_to_iso15919 ---

def test_kannada_to_iso_kannaḍa():
    assert kannada_to_iso15919('ಕನ್ನಡ') == 'kannaḍa'


def test_kannada_to_iso_bengaluru():
    assert kannada_to_iso15919('ಬೆಂಗಳೂರು') == 'beṃgaḻūru'


def test_kannada_to_iso_dharma():
    assert kannada_to_iso15919('ಧರ್ಮ') == 'dharma'


def test_kannada_to_iso_vowels():
    assert kannada_to_iso15919('ಅಇಉ') == 'aiu'


def test_kannada_to_iso_consonant_virama():
    assert kannada_to_iso15919('ಕ್') == 'k'


def test_kannada_to_iso_digits():
    assert kannada_to_iso15919('೧೨೩') == '123'


# --- iso15919_to_kannada ---

def test_iso_to_kannada_kannaḍa():
    assert iso15919_to_kannada('kannaḍa') == 'ಕನ್ನಡ'


def test_iso_to_kannada_dharma():
    assert iso15919_to_kannada('dharma') == 'ಧರ್ಮ'


# --- is_kannada ---

def test_is_kannada_true():
    assert is_kannada('ಕನ್ನಡ') is True


def test_is_kannada_latin_false():
    assert is_kannada('kannada') is False


def test_is_kannada_empty_false():
    assert is_kannada('') is False


# --- normalize_to_iso15919 ---

def test_normalize_kannada_input():
    result = normalize_to_iso15919('ಕನ್ನಡ')
    assert result == 'kannaḍa'


def test_normalize_iso_passthrough():
    assert normalize_to_iso15919('kannaḍa') == 'kannaḍa'
