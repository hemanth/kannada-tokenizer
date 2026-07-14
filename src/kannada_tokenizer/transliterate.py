"""
transliterate.py — Bidirectional Kannada ↔ ISO 15919 transliteration.

This module provides pure-Python, zero-dependency conversion between
Kannada script and ISO 15919 romanization (IAST extended for Dravidian
languages).

Public API
----------
- kannada_to_iso15919(text)     — Convert Kannada text to ISO 15919.
- iso15919_to_kannada(text)     — Convert ISO 15919 text to Kannada.
- is_kannada(text)              — Detect whether a string is primarily Kannada.
- normalize_to_iso15919(text)   — Auto-detect script and return ISO 15919.

Design notes
------------
* All mapping data lives in plain dicts/tuples at module level so tables can be
  maintained, extended, or serialised without touching logic.
* Unicode NFC normalisation is applied at every public entry-point.
* Mixed-script text (e.g. Kannada mixed with ASCII punctuation) is handled
  gracefully: characters outside the relevant script are passed through as-is.
* Kannada distinguishes short e/o (ಎ/ಒ) from long ē/ō (ಏ/ಓ), unlike
  Devanagari. The ISO 15919 standard uses macrons (ē, ō) for the long forms.
* Two-part vowel signs (e.g. ೊ = \u0CC6 + \u0CBE) are handled as single
  precomposed characters after NFC normalization.
"""

from __future__ import annotations

import unicodedata
from typing import Dict, List, Tuple

# ──────────────────────────────────────────────────────────────────────
# §1  Constants — Unicode code-point ranges
# ──────────────────────────────────────────────────────────────────────

# Kannada block: U+0C80 – U+0CFF
_KANNADA_START = 0x0C80
_KANNADA_END = 0x0CFF

# Virama (halant) — suppresses the inherent 'a' vowel
VIRAMA = "\u0CCD"  # ್

# Nukta — modifies a consonant to represent a borrowed sound
NUKTA = "\u0CBC"  # ಼

# Chandrabindu, Anusvara, Visarga
CHANDRABINDU = "\u0C81"  # ಁ
ANUSVARA = "\u0C82"  # ಂ
VISARGA = "\u0C83"  # ಃ

# ──────────────────────────────────────────────────────────────────────
# §2  Mapping tables — Kannada → ISO 15919
# ──────────────────────────────────────────────────────────────────────
#
# Tables are split into logical groups for clarity. Every group is a
# plain dict mapping a *single* Kannada character (or short sequence
# in the case of nukta consonants) to its ISO 15919 equivalent.
#
# For consonants the ISO 15919 value does NOT include the inherent 'a';
# that is inserted by the transliteration engine when no mātrā or
# virama follows.
#
# NOTE: Kannada has a richer vowel inventory than Devanagari — it
# distinguishes short e/o from long ē/ō.  ISO 15919 uses macrons
# for the long forms.

# ----- 2a. Independent vowels (svara) -----
# These appear at the start of a word or after another vowel.
VOWELS_INDEPENDENT: Dict[str, str] = {
    "ಅ": "a",    # U+0C85
    "ಆ": "ā",    # U+0C86
    "ಇ": "i",    # U+0C87
    "ಈ": "ī",    # U+0C88
    "ಉ": "u",    # U+0C89
    "ಊ": "ū",    # U+0C8A
    "ಋ": "ṛ",    # U+0C8B
    "ೠ": "ṝ",    # U+0CE0
    "ಌ": "ḷ",    # U+0C8C
    "ೡ": "ḹ",    # U+0CE1
    "ಎ": "e",    # U+0C8E — short e (Dravidian distinction!)
    "ಏ": "ē",    # U+0C8F — long ē
    "ಐ": "ai",   # U+0C90
    "ಒ": "o",    # U+0C92 — short o (Dravidian distinction!)
    "ಓ": "ō",    # U+0C93 — long ō
    "ಔ": "au",   # U+0C94
}

# ----- 2b. Dependent vowel signs (mātrā) -----
# These attach to a preceding consonant and replace the inherent 'a'.
# Note: there is no mātrā for 'a' because 'a' is the inherent vowel.
#
# Some Kannada vowel signs are "two-part":
#   ೊ (U+0CCA) = ೆ (U+0CC6) + ಾ (U+0CBE)
#   ೋ (U+0CCB) = ೇ (U+0CC7) + ಾ (U+0CBE)
#   ೌ (U+0CCC) = ೆ (U+0CC6) + ೕ (U+0CD5)
# NFC normalization collapses these into the precomposed forms listed below.
VOWELS_DEPENDENT: Dict[str, str] = {
    "\u0CBE": "ā",   # ಾ
    "\u0CBF": "i",   # ಿ
    "\u0CC0": "ī",   # ೀ
    "\u0CC1": "u",   # ು
    "\u0CC2": "ū",   # ೂ
    "\u0CC3": "ṛ",   # ೃ
    "\u0CC4": "ṝ",   # ೄ
    "\u0CE2": "ḷ",   # ೢ
    "\u0CE3": "ḹ",   # ೣ
    "\u0CC6": "e",   # ೆ — short e
    "\u0CC7": "ē",   # ೇ — long ē
    "\u0CC8": "ai",  # ೈ
    "\u0CCA": "o",   # ೊ — short o (precomposed two-part sign)
    "\u0CCB": "ō",   # ೋ — long ō (precomposed two-part sign)
    "\u0CCC": "au",  # ೌ
}

# ----- 2c. Consonants (vyañjana) -----
# Arranged by the traditional varga (class) system, plus Dravidian-specific
# consonants at the end.
CONSONANTS: Dict[str, str] = {
    # -- Velar (kaṇṭhya) --
    "ಕ": "k",     # U+0C95
    "ಖ": "kh",    # U+0C96
    "ಗ": "g",     # U+0C97
    "ಘ": "gh",    # U+0C98
    "ಙ": "ṅ",     # U+0C99
    # -- Palatal (tālavya) --
    "ಚ": "c",     # U+0C9A
    "ಛ": "ch",    # U+0C9B
    "ಜ": "j",     # U+0C9C
    "ಝ": "jh",    # U+0C9D
    "ಞ": "ñ",     # U+0C9E
    # -- Retroflex (mūrdhanya) --
    "ಟ": "ṭ",     # U+0C9F
    "ಠ": "ṭh",    # U+0CA0
    "ಡ": "ḍ",     # U+0CA1
    "ಢ": "ḍh",    # U+0CA2
    "ಣ": "ṇ",     # U+0CA3
    # -- Dental (dantya) --
    "ತ": "t",     # U+0CA4
    "ಥ": "th",    # U+0CA5
    "ದ": "d",     # U+0CA6
    "ಧ": "dh",    # U+0CA7
    "ನ": "n",     # U+0CA8
    # -- Labial (oṣṭhya) --
    "ಪ": "p",     # U+0CAA
    "ಫ": "ph",    # U+0CAB
    "ಬ": "b",     # U+0CAC
    "ಭ": "bh",    # U+0CAD
    "ಮ": "m",     # U+0CAE
    # -- Semi-vowels (antaḥstha) --
    "ಯ": "y",     # U+0CAF
    "ರ": "r",     # U+0CB0
    "ಲ": "l",     # U+0CB2
    "ವ": "v",     # U+0CB5
    # -- Sibilants (ūṣman) --
    "ಶ": "ś",     # U+0CB6
    "ಷ": "ṣ",     # U+0CB7
    "ಸ": "s",     # U+0CB8
    # -- Glottal --
    "ಹ": "h",     # U+0CB9
    # -- Dravidian-specific --
    "ಳ": "ḻ",     # U+0CB3 — retroflex lateral (unique to Dravidian!)
    "ೞ": "ẕ",     # U+0CDE — retroflex approximant (archaic Kannada)
}

# ----- 2d. Nukta consonants (borrowed sounds) -----
# Each is the base consonant + nukta (U+0CBC).
# Less commonly used in Kannada than in Devanagari, but supported for
# loanword representation.
NUKTA_CONSONANTS: Dict[str, str] = {
    "ಕ಼": "q",     # ಕ + ಼
    "ಖ಼": "x",     # ಖ + ಼
    "ಗ಼": "ġ",     # ಗ + ಼
    "ಜ಼": "z",     # ಜ + ಼
    "ಫ಼": "f",     # ಫ + ಼
}

# ----- 2e. Modifiers & signs -----
MODIFIERS: Dict[str, str] = {
    ANUSVARA:     "ṃ",
    VISARGA:      "ḥ",
    CHANDRABINDU: "m̐",   # nasalisation mark
}

# ----- 2f. Kannada digits -----
DIGITS: Dict[str, str] = {
    "೦": "0",   # U+0CE6
    "೧": "1",   # U+0CE7
    "೨": "2",   # U+0CE8
    "೩": "3",   # U+0CE9
    "೪": "4",   # U+0CEA
    "೫": "5",   # U+0CEB
    "೬": "6",   # U+0CEC
    "೭": "7",   # U+0CED
    "೮": "8",   # U+0CEE
    "೯": "9",   # U+0CEF
}

# ----- 2g. Punctuation -----
# Danda and double danda are shared across Indic scripts (Devanagari block).
PUNCTUATION: Dict[str, str] = {
    "\u0964": ".",   # । danda  → full stop
    "\u0965": ".",   # ॥ double danda → full stop
}

# ──────────────────────────────────────────────────────────────────────
# §3  Reverse mapping tables — ISO 15919 → Kannada
# ──────────────────────────────────────────────────────────────────────
#
# Built programmatically from the forward tables where possible, with
# hand-tuned additions for multi-character ISO 15919 sequences that must
# be matched longest-first to avoid ambiguity (e.g. "kh" before "k").

def _invert(d: Dict[str, str]) -> Dict[str, str]:
    """Return {v: k for k, v in d.items()}, preserving first occurrence."""
    inv: Dict[str, str] = {}
    for k, v in d.items():
        if v not in inv:
            inv[v] = k
    return inv


# Independent vowels: ISO 15919 → Kannada independent vowel
_ISO15919_TO_VOWEL_INDEPENDENT: Dict[str, str] = _invert(VOWELS_INDEPENDENT)

# Dependent vowels: ISO 15919 → Kannada mātrā
# 'a' maps to empty string because the inherent vowel needs no mātrā.
_ISO15919_TO_VOWEL_DEPENDENT: Dict[str, str] = _invert(VOWELS_DEPENDENT)
_ISO15919_TO_VOWEL_DEPENDENT["a"] = ""  # inherent vowel — no visible mātrā

# Consonants: ISO 15919 → Kannada base consonant
_ISO15919_TO_CONSONANT: Dict[str, str] = _invert(CONSONANTS)

# Nukta consonants
_ISO15919_TO_NUKTA: Dict[str, str] = _invert(NUKTA_CONSONANTS)

# Modifiers
_ISO15919_TO_MODIFIER: Dict[str, str] = _invert(MODIFIERS)

# Digits
_ISO15919_TO_DIGIT: Dict[str, str] = _invert(DIGITS)

# All ISO 15919 vowel strings (used for lookahead when deciding inherent 'a').
_ALL_ISO15919_VOWELS: set = set(VOWELS_INDEPENDENT.values())

# Set of all Kannada dependent-vowel (mātrā) code-points.
_MATRA_CODEPOINTS: set = set(VOWELS_DEPENDENT.keys())

# Set of all Kannada independent-vowel characters.
_INDEPENDENT_VOWEL_CODEPOINTS: set = set(VOWELS_INDEPENDENT.keys())

# Set of all Kannada consonant characters (without nukta).
_CONSONANT_CODEPOINTS: set = set(CONSONANTS.keys())

# ──────────────────────────────────────────────────────────────────────
# §4  Helper — sorted ISO 15919 tokens for longest-match parsing
# ──────────────────────────────────────────────────────────────────────

def _build_sorted_iso15919_tokens() -> List[Tuple[str, str, str]]:
    """
    Return a list of (iso15919_token, kannada, category) tuples sorted by
    descending token length so that the parser always tries the longest
    match first (e.g. "kh" before "k", "ai" before "a").

    Categories: 'consonant', 'vowel', 'modifier', 'digit', 'nukta'.
    """
    tokens: List[Tuple[str, str, str]] = []

    for iso, kan in _ISO15919_TO_CONSONANT.items():
        tokens.append((iso, kan, "consonant"))
    for iso, kan in _ISO15919_TO_NUKTA.items():
        tokens.append((iso, kan, "nukta"))
    for iso, kan in _ISO15919_TO_VOWEL_INDEPENDENT.items():
        tokens.append((iso, kan, "vowel"))
    for iso, kan in _ISO15919_TO_MODIFIER.items():
        tokens.append((iso, kan, "modifier"))
    for iso, kan in _ISO15919_TO_DIGIT.items():
        tokens.append((iso, kan, "digit"))

    # Sort descending by length so longest tokens are tried first
    tokens.sort(key=lambda t: len(t[0]), reverse=True)
    return tokens


_ISO15919_TOKENS: List[Tuple[str, str, str]] = _build_sorted_iso15919_tokens()

# ──────────────────────────────────────────────────────────────────────
# §5  Core: Kannada → ISO 15919
# ──────────────────────────────────────────────────────────────────────

def _is_kannada_char(ch: str) -> bool:
    """Return True if *ch* falls within the Kannada Unicode block."""
    cp = ord(ch)
    return _KANNADA_START <= cp <= _KANNADA_END


def kannada_to_iso15919(text: str) -> str:
    """
    Convert a Kannada string to ISO 15919.

    The algorithm walks the string character-by-character, maintaining a
    flag ``pending_a`` that tracks whether the inherent vowel 'a' should
    be emitted after a consonant.  The inherent vowel is suppressed when
    a virama or a dependent vowel (mātrā) follows.

    Non-Kannada characters (Latin letters, ASCII punctuation, …) are
    passed through unchanged, which makes the function safe for mixed-
    script input.

    Parameters
    ----------
    text : str
        Input string, possibly containing Kannada characters.

    Returns
    -------
    str
        ISO 15919 transliteration of *text*.
    """
    # Always work with NFC-normalised text so that two-part vowel signs
    # (e.g. ೊ = ೆ + ಾ) are collapsed into their precomposed forms,
    # and nukta sequences (base + U+0CBC) are in canonical form.
    text = unicodedata.normalize("NFC", text)

    out: List[str] = []
    i = 0
    n = len(text)
    pending_a = False  # True when we've just emitted a consonant and may need 'a'

    while i < n:
        ch = text[i]

        # ── Nukta consonants (two-char sequences: base + nukta) ──
        # Check BEFORE single consonants so "ಕ಼" is matched as a unit.
        if i + 1 < n and text[i + 1] == NUKTA:
            pair = text[i : i + 2]
            if pair in NUKTA_CONSONANTS:
                # Flush any pending inherent 'a' from a previous consonant
                if pending_a:
                    out.append("a")
                    pending_a = False
                out.append(NUKTA_CONSONANTS[pair])
                pending_a = True
                i += 2
                continue

        # ── Virama (halant) — kills the inherent vowel ──
        if ch == VIRAMA:
            # Cancel the pending inherent 'a'
            pending_a = False
            i += 1
            continue

        # ── Dependent vowels (mātrā) — replace inherent 'a' ──
        if ch in VOWELS_DEPENDENT:
            # A mātrā always cancels the inherent 'a' and provides its
            # own vowel sound.
            pending_a = False
            out.append(VOWELS_DEPENDENT[ch])
            i += 1
            continue

        # ── Consonants ──
        if ch in CONSONANTS:
            if pending_a:
                out.append("a")
            out.append(CONSONANTS[ch])
            pending_a = True
            i += 1
            continue

        # ── Independent vowels ──
        if ch in VOWELS_INDEPENDENT:
            if pending_a:
                out.append("a")
                pending_a = False
            out.append(VOWELS_INDEPENDENT[ch])
            i += 1
            continue

        # ── Modifiers (anusvara, visarga, chandrabindu) ──
        if ch in MODIFIERS:
            # Modifiers attach to the preceding syllable; flush 'a' first.
            if pending_a:
                out.append("a")
                pending_a = False
            out.append(MODIFIERS[ch])
            i += 1
            continue

        # ── Digits ──
        if ch in DIGITS:
            if pending_a:
                out.append("a")
                pending_a = False
            out.append(DIGITS[ch])
            i += 1
            continue

        # ── Punctuation ──
        if ch in PUNCTUATION:
            if pending_a:
                out.append("a")
                pending_a = False
            out.append(PUNCTUATION[ch])
            i += 1
            continue

        # ── Nukta by itself (shouldn't happen in well-formed text) ──
        if ch == NUKTA:
            i += 1
            continue

        # ── Anything else (Latin, punctuation, whitespace …) ──
        if pending_a:
            out.append("a")
            pending_a = False
        out.append(ch)
        i += 1

    # If the string ends with a consonant that still has a pending 'a'
    if pending_a:
        out.append("a")

    return "".join(out)


# ──────────────────────────────────────────────────────────────────────
# §6  Core: ISO 15919 → Kannada
# ──────────────────────────────────────────────────────────────────────

def _is_iso15919_vowel_at(text: str, pos: int) -> Tuple[bool, str, int]:
    """
    Check whether an ISO 15919 vowel token starts at *pos* in *text*.

    Returns (matched, iso15919_vowel_string, length) on success,
    or (False, '', 0) otherwise.

    Uses longest-match semantics ('ai' before 'a', 'au' before 'a', etc.).
    """
    # Check two-char vowels first, then one-char.
    for length in (2, 1):
        candidate = text[pos : pos + length].lower()
        if candidate in _ISO15919_TO_VOWEL_INDEPENDENT:
            return True, candidate, length
    return False, "", 0


def iso15919_to_kannada(text: str) -> str:
    """
    Convert an ISO 15919 string to Kannada.

    The parser scans *text* from left to right using longest-match
    tokenisation.  It tracks whether the current context is "after a
    consonant" so it can choose between independent vowels and mātrā
    forms, and inserts virama between consecutive consonants.

    Parameters
    ----------
    text : str
        Input string in ISO 15919 (or mixed ISO 15919 / other scripts).

    Returns
    -------
    str
        Kannada transliteration of *text*.
    """
    text = unicodedata.normalize("NFC", text)

    out: List[str] = []
    i = 0
    n = len(text)
    after_consonant = False  # True when the last emitted char was a consonant

    while i < n:
        matched = False

        # Try every token (longest first) against the current position.
        for iso_tok, kan, category in _ISO15919_TOKENS:
            tok_len = len(iso_tok)
            # Case-insensitive comparison for the ISO 15919 token
            if text[i : i + tok_len].lower() == iso_tok.lower():
                if category in ("consonant", "nukta"):
                    if after_consonant:
                        # Previous consonant needs virama before this one
                        out.append(VIRAMA)
                    out.append(kan)
                    after_consonant = True
                elif category == "vowel":
                    if after_consonant:
                        # Use the dependent (mātrā) form and suppress the
                        # inherent 'a'.
                        matra = _ISO15919_TO_VOWEL_DEPENDENT.get(iso_tok.lower(), "")
                        out.append(matra)  # "" for 'a' → no visible mātrā
                        after_consonant = False
                    else:
                        # Word-initial or after another vowel → independent form
                        out.append(kan)
                elif category == "modifier":
                    # Modifiers attach after the syllable
                    if after_consonant:
                        # Implicit 'a' is assumed before the modifier
                        after_consonant = False
                    out.append(kan)
                elif category == "digit":
                    if after_consonant:
                        after_consonant = False
                    out.append(kan)

                i += tok_len
                matched = True
                break

        if not matched:
            # Not an ISO 15919 token — pass through (spaces, ASCII punctuation, …)
            if after_consonant:
                after_consonant = False
            out.append(text[i])
            i += 1

    # If the string ends mid-consonant, we must add a virama to suppress
    # the inherent 'a'.  ISO 15919 is explicit about final vowels, so a bare
    # consonant at end-of-string means the halant form.
    if after_consonant:
        out.append(VIRAMA)

    return "".join(out)


# ──────────────────────────────────────────────────────────────────────
# §7  Detection: is_kannada
# ──────────────────────────────────────────────────────────────────────

def is_kannada(text: str, threshold: float = 0.5) -> bool:
    """
    Return ``True`` if *text* is primarily written in Kannada script.

    The heuristic counts how many *non-whitespace* characters fall inside
    the Kannada Unicode block and returns ``True`` when the ratio meets
    or exceeds *threshold* (default 50 %).

    Parameters
    ----------
    text : str
        The text to inspect.
    threshold : float
        Minimum fraction of Kannada characters (among scriptable
        characters) to consider the text "Kannada".  Defaults to 0.5.

    Returns
    -------
    bool
    """
    if not text:
        return False

    text = unicodedata.normalize("NFC", text)

    total = 0
    kannada_count = 0
    for ch in text:
        # Skip whitespace for the ratio
        if ch.isspace():
            continue
        total += 1
        if _is_kannada_char(ch):
            kannada_count += 1

    if total == 0:
        return False
    return (kannada_count / total) >= threshold


# ──────────────────────────────────────────────────────────────────────
# §8  Convenience: normalize_to_iso15919
# ──────────────────────────────────────────────────────────────────────

def normalize_to_iso15919(text: str) -> str:
    """
    Auto-detect the script of *text* and return its ISO 15919 representation.

    - If *text* is detected as Kannada, it is transliterated to ISO 15919.
    - Otherwise it is returned as-is (assumed to already be ISO 15919 or some
      other Latin-based notation).

    Parameters
    ----------
    text : str
        Input string in Kannada or ISO 15919.

    Returns
    -------
    str
        ISO 15919 representation of *text*.
    """
    text = unicodedata.normalize("NFC", text)
    if is_kannada(text):
        return kannada_to_iso15919(text)
    return text
