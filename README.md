# kannada-tokenizer

Tokenize Kannada text with sandhi splitting for Information Retrieval.

```bash
pip install kannada-tokenizer
```

## Quick start

```python
from kannada_tokenizer import tokenize

tokenize("ಕನ್ನಡ ಧರ್ಮ")
# ['ಕನ್ನಡ', 'ಧರ್ಮ']

tokenize("dharma yōga")
# ['ಧರ್ಮ', 'ಯೋಗ']
```

`tokenize()` accepts both Kannada script and ISO 15919 romanized input. Splits on whitespace and punctuation, applies reverse sandhi rules, and outputs Kannada script.

## Sandhi splitting

```python
from kannada_tokenizer.sandhi import split_sandhi

split_sandhi("rāmāyana")   # lōpa sandhi: ā → a + ā
# ['rāma', 'āyana']

split_sandhi("kannaḍa")    # no junction found
# ['kannaḍa']
```

Rule-based engine covering lōpa sandhi (vowel elision), āgama sandhi (y/v insertion), ādeśa sandhi (guṇa-like substitution), and consonant sandhi (voicing, gemination, nasals). Sandhi engine works in ISO 15919 internally.

## Transliteration

```python
from kannada_tokenizer.transliterate import (
    kannada_to_iso15919,
    iso15919_to_kannada,
    is_kannada,
)

kannada_to_iso15919("ಬೆಂಗಳೂರು")
# 'beṃgaḻūru'

iso15919_to_kannada("kannaḍa")
# 'ಕನ್ನಡ'

is_kannada("ಕನ್ನಡ")
# True
```

Handles Kannada's short/long e/o distinction (ಎ→e vs ಏ→ē) and the retroflex lateral ಳ→ḻ unique to Dravidian.

## Word-level tokenization

```python
from kannada_tokenizer.tokenizer import tokenize_words

tokenize_words("ಧರ್ಮ ಯೋಗ")
# ['ಧರ್ಮ', 'ಯೋಗ']
```

`tokenize_words()` splits on whitespace and punctuation only — no sandhi splitting.

## CLI

```bash
kannada-tokenize "ಕನ್ನಡ ಧರ್ಮ"
# ಕನ್ನಡ
# ಧರ್ಮ

echo "dharma yōga" | kannada-tokenize
# ಧರ್ಮ
# ಯೋಗ

kannada-tokenize --no-sandhi "ಕನ್ನಡ"
# ಕನ್ನಡ

kannada-tokenize -s " " "ಧರ್ಮ ಯೋಗ"
# ಧರ್ಮ ಯೋಗ
```

- `--no-sandhi` — word-level only, skip sandhi splitting
- `--separator SEP` — output separator (default: newline)

## License

MIT © [Hemanth.HM](https://h3manth.com)
