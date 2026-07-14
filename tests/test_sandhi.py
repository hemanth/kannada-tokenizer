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


def test_sandhi_kannada_script_no_split():
    assert split_sandhi('ಕನ್ನಡ') == ['ಕನ್ನಡ']
    assert split_sandhi('ಧರ್ಮ') == ['ಧರ್ಮ']


def test_sandhi_kannada_script_returns_kannada():
    result = split_sandhi('ರಾಮಾಯಣ')
    for tok in result:
        assert any(0x0C80 <= ord(c) <= 0x0CFF for c in tok), (
            f"Token '{tok}' is not in Kannada script"
        )
