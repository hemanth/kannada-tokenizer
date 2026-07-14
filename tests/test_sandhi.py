"""Tests for the sandhi module."""

from kannada_tokenizer.sandhi import split_sandhi


def test_sandhi_no_split_dharma():
    assert split_sandhi('dharma') == ['dharma']


def test_sandhi_no_split_yoga():
    assert split_sandhi('yōga') == ['yōga']


def test_sandhi_no_split_kannada():
    assert split_sandhi('kannaḍa') == ['kannaḍa']


def test_sandhi_simple_words_unsplit():
    for word in ('karma', 'guru', 'dēva'):
        result = split_sandhi(word)
        assert result == [word], f"Expected [{word}], got {result}"
