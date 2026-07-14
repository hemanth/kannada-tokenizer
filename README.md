# kannada-tokenizer

Tokenize Kannada text with sandhi splitting for Information Retrieval.

```bash
pip install kannada-tokenizer
```

## Quick start

```python
from kannada_tokenizer import tokenize

tokenize("ಬೆಂಗಳೂರು ಭಾರತದ ಸಿಲಿಕಾನ್ ಕಣಿವೆ")
# ['ಬೆಂಗಳೂರು', 'ಭಾರತದ', 'ಸಿಲಿಕಾನ್', 'ಕಣಿವೆ']

tokenize("ವಿದ್ಯಾಲಯದಲ್ಲಿ ಮಕ್ಕಳು ಕಲಿಯುತ್ತಾರೆ")
# ['ವಿದ್ಯಾಲಯದಲ್ಲಿ', 'ಮಕ್ಕಳು', 'ಕಲಿಯುತ್ತಾರೆ']

tokenize("ದೇವಾಲಯದ ಮಹೋತ್ಸವ")
# ['ದೇವಾಲಯದ', 'ಮಹೋತ್ಸವ']
```

`tokenize()` accepts both Kannada script and ISO 15919 romanized input. Splits on whitespace and punctuation, applies reverse sandhi rules, and outputs Kannada script.

## Sandhi splitting

```python
from kannada_tokenizer.sandhi import split_sandhi

split_sandhi("ರಾಮಾಯಣ")    # savarṇa-dīrgha: a + ā → ā
# ['ರಾಮ', 'ಆಯಣ']

split_sandhi("ದೇವಾಲಯ")    # lōpa: a + ā → ā
# ['ದೇವ', 'ಆಲಯ']

split_sandhi("ವಿದ್ಯಾಲಯ")   # lōpa: a + ā → ā
# ['ವಿದ್ಯ', 'ಆಲಯ']

split_sandhi("ಸರ್ವಜ್ಞ")    # lōpa: a + a → a
# ['ಸರ್ವ', 'ಅಜ್ಞ']

split_sandhi("ಕನ್ನಡ")      # no junction found
# ['ಕನ್ನಡ']
```

Accepts Kannada script or ISO 15919 — output script matches input. Rule-based engine covering lōpa sandhi (vowel elision), āgama sandhi (y/v insertion), ādeśa sandhi (guṇa-like substitution), and consonant sandhi (voicing, gemination, nasals).

## Transliteration

```python
from kannada_tokenizer.transliterate import (
    kannada_to_iso15919,
    iso15919_to_kannada,
    is_kannada,
)

kannada_to_iso15919("ಶ್ರೀರಂಗಪಟ್ಟಣ")
# 'śrīraṃgapaṭṭaṇa'

kannada_to_iso15919("ಜ್ಞಾನಪೀಠ")
# 'jñānapīṭha'

iso15919_to_kannada("mahārāṣṭra")
# 'ಮಹಾರಾಷ್ಟ್ರ'

kannada_to_iso15919("ಬೆಂಗಳೂರು")
# 'beṃgaḻūru'

is_kannada("ಕುವೆಂಪು")
# True
```

Handles Kannada's short/long e/o distinction (ಎ→e vs ಏ→ē), the retroflex lateral ಳ→ḻ, conjunct consonants (ಕ್ಷ, ಜ್ಞ, ಶ್ರೀ), and perfect round-trip fidelity.

## Word-level tokenization

```python
from kannada_tokenizer.tokenizer import tokenize_words

tokenize_words("ಮಹಾತ್ಮ ಗಾಂಧಿ ರಾಷ್ಟ್ರಪಿತ")
# ['ಮಹಾತ್ಮ', 'ಗಾಂಧಿ', 'ರಾಷ್ಟ್ರಪಿತ']
```

`tokenize_words()` splits on whitespace and punctuation only — no sandhi splitting.

## CLI

```bash
kannada-tokenize "ಕನ್ನಡ ನಾಡಿನ ಭಾಷೆ"
# ಕನ್ನಡ
# ನಾಡಿನ
# ಭಾಷೆ

echo "ವಿದ್ಯಾಲಯದಲ್ಲಿ ಮಕ್ಕಳು ಕಲಿಯುತ್ತಾರೆ" | kannada-tokenize
# ವಿದ್ಯಾಲಯದಲ್ಲಿ
# ಮಕ್ಕಳು
# ಕಲಿಯುತ್ತಾರೆ

kannada-tokenize -s " " "ಬೆಂಗಳೂರು ಮಹಾನಗರ"
# ಬೆಂಗಳೂರು ಮಹಾನಗರ
```

- `--no-sandhi` — word-level only, skip sandhi splitting
- `--separator SEP` — output separator (default: newline)

## License

MIT © [Hemanth.HM](https://h3manth.com)
