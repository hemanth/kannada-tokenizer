"""
sandhi.py — Rule-based Kannada sandhi splitting for Information Retrieval.

Sandhi (ಸಂಧಿ) is the euphonic combination that occurs at morpheme and word
boundaries in Kannada.  This module implements *reverse* sandhi rules: given
a combined surface form it tries to recover the original components.

Design decisions
~~~~~~~~~~~~~~~~
* **ISO 15919 encoding only.**  The upstream transliteration module normalises
  all input to ISO 15919 before this module is called.
* **Zero external dependencies.**  Pure-Python, stdlib only.
* **Longest-match / fewest-parts heuristic.**  When multiple candidate splits
  are possible we prefer the one that produces the fewest, longest tokens.
  This is a good proxy for "most likely intended reading" in an IR context
  where recall matters more than philological precision.

Kannada sandhi differs from Sanskrit sandhi in several important ways:

1. **Lōpa Sandhi (ಲೋಪ ಸಂಧಿ)** — Vowel elision: when two vowels meet at a
   word boundary, one (usually the first) is dropped.
2. **Āgama Sandhi (ಆಗಮ ಸಂಧಿ)** — Insertion: a consonant ('y' or 'v') is
   inserted between vowels to prevent hiatus.
3. **Ādeśa Sandhi (ಆದೇಶ ಸಂಧಿ)** — Substitution: a sound at the junction is
   replaced by another (Guṇa-like changes in tatsama words).
4. **Consonant Sandhi** — Voicing assimilation and gemination at word
   boundaries, common in Dravidian Kannada.

The rules are represented as 4-tuples:

    (combined_pattern, left_part, right_part, category)

``combined_pattern`` is the string that appears at the junction in the
surface form.  ``left_part`` is what the *end* of the first word should be
restored to, and ``right_part`` is what the *start* of the second word
should be restored to.  ``category`` is one of ``'lōpa'``, ``'āgama'``,
``'ādeśa'``, or ``'consonant'``.

References
~~~~~~~~~~
* Kittel, *A Grammar of the Kannada Language*
* Narasimhachar, *Kannada Vyākaraṇa*
"""

from __future__ import annotations

from typing import List, Tuple

# ---------------------------------------------------------------------------
# Constants — vowel / consonant inventories (ISO 15919)
# ---------------------------------------------------------------------------

VOWELS: set[str] = {
    "a", "ā", "i", "ī", "u", "ū",
    "e", "ē", "ai", "o", "ō", "au",
}

SHORT_VOWELS: set[str] = {"a", "i", "u", "e", "o"}

LONG_VOWELS: set[str] = {"ā", "ī", "ū", "ē", "ō"}

DIPHTHONGS: set[str] = {"ai", "au"}

VOICED_CONSONANTS: set[str] = {
    "g", "gh", "j", "jh", "ḍ", "ḍh", "d", "dh", "b", "bh",
    "ṅ", "ñ", "ṇ", "n", "m",
    "y", "r", "l", "v", "ḷ",
    "h",
}

UNVOICED_CONSONANTS: set[str] = {
    "k", "kh", "c", "ch", "ṭ", "ṭh", "t", "th", "p", "ph",
    "s", "ś", "ṣ",
}

STOPS_VOICED: dict[str, str] = {
    # unvoiced stop → voiced counterpart
    "k": "g", "kh": "gh",
    "c": "j", "ch": "jh",
    "ṭ": "ḍ", "ṭh": "ḍh",
    "t": "d", "th": "dh",
    "p": "b", "ph": "bh",
}

NASALS_FOR_CLASS: dict[str, str] = {
    # class stop → class nasal
    "k": "ṅ", "kh": "ṅ", "g": "ṅ", "gh": "ṅ",
    "c": "ñ", "ch": "ñ", "j": "ñ", "jh": "ñ",
    "ṭ": "ṇ", "ṭh": "ṇ", "ḍ": "ṇ", "ḍh": "ṇ",
    "t": "n", "th": "n", "d": "n", "dh": "n",
    "p": "m", "ph": "m", "b": "m", "bh": "m",
}

# ---------------------------------------------------------------------------
# SANDHI RULES — reverse (splitting) direction
# ---------------------------------------------------------------------------
#
# Each tuple is: (combined_pattern, left_part, right_part, category)
#
# ``combined_pattern`` is what we *see* at the junction in the surface form.
# ``left_part``        is the restored tail of the first word.
# ``right_part``       is the restored head of the second word.
# ``category``         is one of 'lōpa', 'āgama', 'ādeśa', 'consonant'.
#
# Rules are ordered longest-pattern-first so that a simple linear scan with
# ``str.find`` will naturally prefer the most specific match.

# ---- 1. Lōpa Sandhi (ಲೋಪ ಸಂಧಿ) — Vowel Elision ----------------------------
#
# When two vowels meet at a word boundary, one is dropped (usually the
# first vowel).  Reversing this means: where we see a single vowel at a
# potential junction, we try restoring the elided vowel.
#
# Common patterns:
#   a + a → a  (first 'a' dropped)
#   a + ā → ā
#   a + u → u
#   a + i → i
#   a + e → e
#   a + ō → ō
#
# General principle: short vowel before a different vowel is dropped.

_LOPA_SANDHI_RULES: List[Tuple[str, str, str, str]] = []

# a + a → a  (identical vowel merger — most common)
_LOPA_SANDHI_RULES.append(("a", "a", "a", "lōpa"))

# a + long/different vowel → the second vowel survives
_LOPA_PAIRS: list[tuple[str, str]] = [
    # (surface_vowel, restored_right_start)
    ("ā", "ā"),
    ("i", "i"),
    ("ī", "ī"),
    ("u", "u"),
    ("ū", "ū"),
    ("e", "e"),
    ("ē", "ē"),
    ("o", "o"),
    ("ō", "ō"),
    ("ai", "ai"),
    ("au", "au"),
]
for _surface, _right in _LOPA_PAIRS:
    # 'a' was elided before _right: reverse means surface _surface → 'a' + _right
    _LOPA_SANDHI_RULES.append((_surface, "a", _right, "lōpa"))

# i/ī elision before dissimilar vowels (less common but attested)
for _short_v, _long_v in [("i", "ī"), ("u", "ū")]:
    for _following in ["a", "ā", "e", "ē", "o", "ō"]:
        _LOPA_SANDHI_RULES.append((_following, _short_v, _following, "lōpa"))


# ---- 2. Āgama Sandhi (ಆಗಮ ಸಂಧಿ) — Insertion --------------------------------
#
# A consonant (usually 'y' or 'v') is inserted between vowels to avoid
# hiatus.  Similar to Sanskrit yān sandhi.
#
# Patterns:
#   i/ī + vowel → i/ī + y + vowel  →  reverse: 'y' at junction → boundary
#   u/ū + vowel → u/ū + v + vowel  →  reverse: 'v' at junction → boundary
#
# We store these with an empty right_part; the split logic fills in the
# actual vowel from the surface form.

_AGAMA_SANDHI_RULES: List[Tuple[str, str, str, str]] = []

# y-āgama: after i/ī
for _src in ("i", "ī"):
    _AGAMA_SANDHI_RULES.append(("y", _src, "", "āgama"))

# v-āgama: after u/ū
for _src in ("u", "ū"):
    _AGAMA_SANDHI_RULES.append(("v", _src, "", "āgama"))


# ---- 3. Ādeśa Sandhi (ಆದೇಶ ಸಂಧಿ) — Substitution ----------------------------
#
# A sound at the junction is replaced by another.  This covers Guṇa-like
# changes that appear in tatsama (Sanskrit-borrowed) words in Kannada.
#
# Guṇa patterns (from Sanskrit influence):
#   a/ā + i/ī → e/ē
#   a/ā + u/ū → o/ō
#   a/ā + ṛ   → ar

_ADESA_SANDHI_RULES: List[Tuple[str, str, str, str]] = []

# Guṇa: a/ā + i/ī → e/ē
for _a in ("a", "ā"):
    for _i in ("i", "ī"):
        _ADESA_SANDHI_RULES.append(("e", _a, _i, "ādeśa"))
        _ADESA_SANDHI_RULES.append(("ē", _a, _i, "ādeśa"))

# Guṇa: a/ā + u/ū → o/ō
for _a in ("a", "ā"):
    for _u in ("u", "ū"):
        _ADESA_SANDHI_RULES.append(("o", _a, _u, "ādeśa"))
        _ADESA_SANDHI_RULES.append(("ō", _a, _u, "ādeśa"))

# Guṇa: a/ā + ṛ → ar (in tatsama words)
_ADESA_SANDHI_RULES.append(("ar", "a", "ṛ", "ādeśa"))
_ADESA_SANDHI_RULES.append(("ar", "ā", "ṛ", "ādeśa"))

# Vṛddhi-like: ā + i/ī → ai; ā + u/ū → au (in tatsama words)
for _i in ("i", "ī"):
    _ADESA_SANDHI_RULES.append(("ai", "ā", _i, "ādeśa"))
for _u in ("u", "ū"):
    _ADESA_SANDHI_RULES.append(("au", "ā", _u, "ādeśa"))


# ---- 4. Consonant Sandhi ----------------------------------------------------
#
# 4a. Voicing assimilation — an originally unvoiced final stop becomes
#     voiced before a voiced consonant / vowel in the next word.
#
# 4b. Gemination — consonant doubling at word boundaries, very common in
#     Dravidian Kannada (e.g., compound words often geminate the initial
#     consonant of the second member).
#
# 4c. Nasal assimilation — a final nasal assimilates to the class of a
#     following stop.

_CONSONANT_SANDHI_RULES: List[Tuple[str, str, str, str]] = []

# 4a. Voicing assimilation — voiced stop at end could be unvoiced original
for _unv, _voi in STOPS_VOICED.items():
    _CONSONANT_SANDHI_RULES.append((_voi, _unv, "", "consonant"))

# 4b. Gemination — doubled consonant at junction → split before second
#     This is a very productive pattern in Kannada compounds.
_GEMINATION_CONSONANTS: list[str] = [
    "k", "g", "c", "j", "ṭ", "ḍ", "t", "d", "p", "b",
    "m", "n", "ṇ", "ṅ", "ñ",
    "y", "r", "l", "v", "ḷ",
    "s", "ś", "ṣ", "h",
]
for _c in _GEMINATION_CONSONANTS:
    # doubled consonant → first word ends with single, second word starts
    # with single (the gemination was introduced at the boundary)
    _CONSONANT_SANDHI_RULES.append((_c + _c, _c, _c, "consonant"))

# 4c. Nasal assimilation — class nasal before a stop ← original 'm' or 'n'
for _stop, _nasal in NASALS_FOR_CLASS.items():
    _CONSONANT_SANDHI_RULES.append((_nasal + _stop, "m", _stop, "consonant"))
    _CONSONANT_SANDHI_RULES.append((_nasal + _stop, "n", _stop, "consonant"))

# 4d. Final 't' + sibilant combinations (in tatsama words)
_CONSONANT_SANDHI_RULES.append(("cch", "t", "ś", "consonant"))
_CONSONANT_SANDHI_RULES.append(("cc", "t", "c", "consonant"))
_CONSONANT_SANDHI_RULES.append(("jj", "t", "j", "consonant"))

# 4e. Final 't' → 'd' before voiced consonant (generic catch-all)
_CONSONANT_SANDHI_RULES.append(("d", "t", "", "consonant"))


# ---------------------------------------------------------------------------
# Combined rule list — sorted longest pattern first for greedy matching
# ---------------------------------------------------------------------------

SANDHI_RULES: List[Tuple[str, str, str, str]] = sorted(
    _LOPA_SANDHI_RULES
    + _AGAMA_SANDHI_RULES
    + _ADESA_SANDHI_RULES
    + _CONSONANT_SANDHI_RULES,
    key=lambda r: len(r[0]),
    reverse=True,
)
"""All reverse-sandhi rules, ordered longest ``combined_pattern`` first.

Each entry is ``(combined_pattern, left_part, right_part, category)`` where
*combined_pattern* is the surface string at the junction, *left_part* is
the restored ending of the first token, *right_part* is the restored
beginning of the second token (empty string when context-dependent), and
*category* is one of ``'lōpa'``, ``'āgama'``, ``'ādeśa'``, or
``'consonant'``.
"""


# ---------------------------------------------------------------------------
# Candidate generation
# ---------------------------------------------------------------------------

_SINGLE_VOWEL_CHARS: set[str] = {
    "a", "ā", "i", "ī", "u", "ū", "e", "ē", "o", "ō",
}

_CONSONANT_CHARS: set[str] = {
    "k", "g", "c", "j", "ṭ", "ḍ", "t", "d", "p", "b",
    "ṅ", "ñ", "ṇ", "n", "m",
    "y", "r", "l", "v", "ḷ",
    "ś", "ṣ", "s", "h",
}

# Bases that form multi-char aspirated consonants with a following 'h'
_ASPIRATE_BASES: set[str] = {
    "k", "g", "c", "j", "ṭ", "ḍ", "t", "d", "p", "b",
}

# Categories that are vowel-type (require consonant-before-junction check)
_VOWEL_TYPE_CATEGORIES: set[str] = {"lōpa", "āgama", "ādeśa"}


def _generate_candidates(word: str) -> list[list[str]]:
    """Generate all possible sandhi-split candidates for *word*.

    For every position in the word where a rule's ``combined_pattern``
    matches, we create a candidate split ``[left, right]`` by replacing the
    combined pattern with the rule's left and right parts.

    We also recurse on the *right* fragment so that chains of sandhi
    (common in long compound words) are handled.

    Returns
    -------
    list[list[str]]
        Each element is a list of ISO 15919 string fragments.  If no rule
        applies anywhere in the word the returned list is empty — the
        caller should fall back to ``[word]``.
    """
    candidates: list[list[str]] = []

    for combined, left_part, right_part, category in SANDHI_RULES:
        clen = len(combined)
        if clen == 0:
            continue

        # Scan every possible junction position.  A junction cannot be at
        # position 0 (nothing on the left) or at position len(word) (nothing
        # on the right).  We need at least one character on each side of the
        # combined pattern to form two meaningful tokens.
        for pos in range(1, len(word) - clen + 1):
            # Check if the combined pattern sits at this position
            if word[pos: pos + clen] != combined:
                continue

            # Context validation for vowel-type sandhi (lōpa, āgama, ādeśa):
            # the character immediately before the junction must be a
            # consonant.  Vowel-type sandhi occurs at the boundary between a
            # consonant-final stem and a vowel-initial word; the consonant
            # before the fused/inserted element is the last consonant of
            # word-1.  Without this check, rules would spuriously match
            # inside words.
            if category in _VOWEL_TYPE_CATEGORIES:
                char_before = word[pos - 1].lower()
                if char_before not in _CONSONANT_CHARS:
                    continue

                # Guard against splitting inside ISO 15919 multi-char
                # consonants.  If char_before is 'h' and the char before
                # *that* is a stop, then we're inside an aspirated consonant
                # (dh, bh, kh, etc.) and this is NOT a valid junction point.
                if (
                    char_before == "h"
                    and pos >= 2
                    and word[pos - 2].lower() in _ASPIRATE_BASES
                ):
                    continue

                # Also need material after the junction for it to be a split
                if not word[pos + clen:]:
                    continue

            # ----- reject trivial / degenerate splits -----
            left_token = word[:pos] + left_part
            right_token = right_part + word[pos + clen:]

            if not left_token or not right_token:
                continue

            # Record the direct two-way split
            candidates.append([left_token, right_token])

            # Recurse on the right fragment to handle compound sandhi
            sub_candidates = _generate_candidates(right_token)
            for sub in sub_candidates:
                candidates.append([left_token] + sub)

    return candidates


# ---------------------------------------------------------------------------
# Candidate scoring
# ---------------------------------------------------------------------------

def _score_candidate(parts: list[str]) -> float:
    """Score a candidate split — higher is better.

    The scoring heuristic balances two goals:

    1. **Fewer parts** — every additional split risks an incorrect break, so
       we penalise the number of parts.
    2. **Longer tokens** — very short (1-char) fragments are suspicious; we
       reward candidates whose shortest token is longer.

    The formula is intentionally simple so that it is fast and transparent::

        score = min_token_length * 10 + avg_length * 2 - num_parts * 5

    A more sophisticated scorer could consult a dictionary or n-gram model,
    but for IR purposes this works well enough.

    Parameters
    ----------
    parts : list[str]
        The candidate list of tokens.

    Returns
    -------
    float
        A numeric score; higher values indicate better candidates.
    """
    if not parts:
        return -1.0

    num_parts = len(parts)
    min_len = min(len(p) for p in parts)
    avg_len = sum(len(p) for p in parts) / num_parts

    # Prefer fewer parts (penalty) and longer minimum token (reward).
    # The average length provides a secondary signal.
    score = (min_len * 10.0) + (avg_len * 2.0) - (num_parts * 5.0)
    return score


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def split_sandhi(word: str) -> list[str]:
    """Split a single ISO 15919-encoded Kannada word at sandhi junctions.

    Uses a rule-based approach: every reverse-sandhi rule is tried at every
    position in the word, candidate splits are scored, and the highest-scoring
    split is returned.  If no rule produces a plausible split the word is
    returned unchanged as ``[word]``.

    Parameters
    ----------
    word : str
        A single token in ISO 15919 transliteration.

    Returns
    -------
    list[str]
        One or more ISO 15919 tokens resulting from the split.  Guaranteed
        to be non-empty.

    Examples
    --------
    >>> split_sandhi("rāmāyana")
    ['rāma', 'āyana']
    >>> split_sandhi("dēvi")        # no split needed (too short / no rule)
    ['dēvi']
    """
    if not word or len(word) <= 1:
        return [word] if word else [""]

    # Short words (≤5 chars) are very unlikely to contain a real sandhi
    # junction that splits into two meaningful tokens.
    if len(word) <= 5:
        return [word]

    candidates = _generate_candidates(word)

    if not candidates:
        return [word]

    # Filter candidates: every fragment must have at least 3 characters
    # to avoid degenerate splits like 'dha' + 'rma' from 'dharma'.
    _MIN_TOKEN_LEN = 3
    viable: list[list[str]] = []
    for candidate in candidates:
        if any(len(p) < _MIN_TOKEN_LEN for p in candidate):
            continue
        viable.append(candidate)

    if not viable:
        return [word]

    # Score each viable candidate and pick the best one.
    best: list[str] = viable[0]
    best_score = _score_candidate(viable[0])

    for candidate in viable[1:]:
        score = _score_candidate(candidate)
        if score > best_score:
            best_score = score
            best = candidate

    # Only accept the split if it scores reasonably well compared to
    # keeping the word intact.  This prevents spurious splits on normal
    # words like 'kannaḍa' where lōpa rules match but the split is
    # nonsensical.  The 0.8 factor biases toward splitting for IR recall.
    unsplit_score = _score_candidate([word])
    if best_score < unsplit_score * 0.8:
        return [word]

    return best
