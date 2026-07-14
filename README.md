# kannada-tokenizer

Tokenize Kannada text with sandhi splitting for Information Retrieval.

```bash
pip install kannada-tokenizer
```

## Quick start

```python
from kannada_tokenizer import tokenize

tokenize("ಕನ್ನಡ ಧರ್ಮ")
# ['kannaḍa', 'dharma']

tokenize("vidyālaya")
# ['vidyālaya']

tokenize("mahōtsava")
# ['maha', 'ōtsava']
```

`tokenize()` normalizes to ISO 15919, splits on whitespace and punctuation, then applies reverse sandhi rules. Accepts both Kannada script and romanized input.

## Sandhi splitting

```python
from kannada_tokenizer.sandhi import split_sandhi

split_sandhi("rāmāyana")   # lōpa sandhi: ā → a + ā
# ['rāma', 'āyana']

split_sandhi("kannaḍa")    # no junction found
# ['kannaḍa']
```

Rule-based engine covering lōpa sandhi (vowel elision), āgama sandhi (y/v insertion), ādeśa sandhi (guṇa-like substitution), and consonant sandhi (voicing, gemination, nasals). Uses longest-match heuristic when splits are ambiguous.

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

tokenize_words("vidyālaya namaḥ")
# ['vidyālaya', 'namaḥ']
```

`tokenize_words()` splits on whitespace and punctuation only — no sandhi splitting.

## CLI

```bash
kannada-tokenize "ಕನ್ನಡ ಧರ್ಮ"
# kannaḍa
# dharma

echo "vidyālaya" | kannada-tokenize
# vidyālaya

kannada-tokenize --no-sandhi "mahōtsava"
# mahōtsava

kannada-tokenize -s " " "dharma yōga"
# dharma yōga
```

- `--no-sandhi` — word-level only, skip sandhi splitting
- `--separator SEP` — output separator (default: newline)

## License

MIT © [Hemanth.HM](https://h3manth.com)
