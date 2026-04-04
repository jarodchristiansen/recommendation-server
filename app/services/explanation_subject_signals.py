"""
Layered subject overlap for deterministic explanations.

Precedence when finding shared labels for thematic copy:
1. Exact match on alias-normalized full subject phrases (set intersection).
2. Same, after applying SUBJECT_ALIAS to each phrase.
3. Token / substring overlap (seed tokens appear in rec subjects or vice versa).
4. Head-subject bias: same as (3) but seed tokens are taken only from the first two seed subjects first.
"""

from __future__ import annotations

import re
from typing import Optional

# Expand over time from real Open Library ↔ Zilliz mismatches.
SUBJECT_ALIAS: dict[str, str] = {
    "sci-fi": "science fiction",
    "sci fi": "science fiction",
    "scifi": "science fiction",
    "sf": "science fiction",
    "fantasy fiction": "fantasy",
    "historic fiction": "historical fiction",
    "spy fiction": "espionage",
    "adventure fiction": "adventure",
}

# Tokens shorter than this are ignored for fuzzy overlap.
_MIN_TOKEN_LEN = 3

_TOKEN_STOPWORDS = frozenset(
    {
        "and",
        "the",
        "for",
        "with",
        "from",
        "fiction",
        "novel",
        "novels",
        "book",
        "books",
        "story",
        "stories",
        "genre",
        "literature",
        "contemporary",
        "american",
        "british",
        "english",
    }
)


def parse_subjects_csv(subjects_csv: str) -> list[str]:
    """Normalize Zilliz CSV subjects string to a list of raw lowercase phrases."""
    if not subjects_csv:
        return []
    return [s.strip().lower() for s in subjects_csv.split(",") if s.strip()]


def _lower_strip_list(subjects: list[str]) -> list[str]:
    return [s.strip().lower() for s in subjects if s and str(s).strip()]


def _apply_aliases(phrase: str) -> str:
    """Map known synonyms; longest keys first if we add multi-word keys later."""
    p = phrase.strip().lower()
    for key in sorted(SUBJECT_ALIAS.keys(), key=len, reverse=True):
        if key in p:
            p = p.replace(key, SUBJECT_ALIAS[key])
    p = re.sub(r"\s+", " ", p).strip()
    return p


def _normalized_phrases(phrases: list[str], *, use_alias: bool) -> set[str]:
    out: set[str] = set()
    for ph in phrases:
        raw = ph.strip().lower()
        if not raw:
            continue
        out.add(_apply_aliases(raw) if use_alias else raw)
    return out


def jaccard_overlap(set_a: list[str], set_b: list[str]) -> tuple[float, list[str]]:
    """Return (score, shared_items). Score is 0.0 if either set is empty."""
    a, b = set(set_a), set(set_b)
    if not a or not b:
        return 0.0, []
    intersection = a & b
    union = a | b
    return len(intersection) / len(union), sorted(intersection)


def _display_from_normalized(norm: str) -> str:
    """Title-style display for a normalized subject phrase."""
    return norm.title() if norm else ""


def _tokens_from_phrase(phrase: str) -> set[str]:
    parts = re.split(r"[^a-z0-9]+", phrase.lower())
    return {
        p
        for p in parts
        if len(p) >= _MIN_TOKEN_LEN and p not in _TOKEN_STOPWORDS
    }


def _token_overlap_display(
    seed_phrases: list[str],
    rec_phrases: list[str],
) -> Optional[list[str]]:
    """Return up to 3 display labels from shared substantive tokens."""
    seed_tokens: set[str] = set()
    for ph in seed_phrases:
        seed_tokens |= _tokens_from_phrase(ph)
    if not seed_tokens:
        return None

    rec_blob = " ".join(rec_phrases)
    matched: list[str] = []
    for t in sorted(seed_tokens):
        if t in rec_blob or any(t in rph for rph in rec_phrases):
            matched.append(t.title())
        if len(matched) >= 3:
            break
    return matched[:3] if matched else None


def find_shared_subject_labels(
    seed_subjects: list[str],
    rec_subjects_parsed: list[str],
) -> Optional[list[str]]:
    """
    Layered subject overlap. Returns display-ready labels (short list) or None.

    rec_subjects_parsed: output of parse_subjects_csv.
    """
    seed_list = _lower_strip_list(seed_subjects)
    rec_list = [s for s in rec_subjects_parsed if s]

    if not seed_list or not rec_list:
        return None

    # Layer 1: exact normalized phrase match (no alias)
    n_seed = _normalized_phrases(seed_list, use_alias=False)
    n_rec = _normalized_phrases(rec_list, use_alias=False)
    inter = n_seed & n_rec
    if inter:
        return [_display_from_normalized(s) for s in sorted(inter)[:3]]

    # Layer 2: alias-normalized phrase match
    a_seed = _normalized_phrases(seed_list, use_alias=True)
    a_rec = _normalized_phrases(rec_list, use_alias=True)
    inter_a = a_seed & a_rec
    if inter_a:
        return [_display_from_normalized(s) for s in sorted(inter_a)[:3]]

    # Layer 2b: alias-normalized containment (e.g. science fiction ⊂ science fiction adventures)
    _min_contain = 4
    for s in sorted(a_seed):
        if len(s) < _min_contain:
            continue
        for r in sorted(a_rec):
            if s in r or (len(r) >= _min_contain and r in s):
                shorter = s if len(s) <= len(r) else r
                return [_display_from_normalized(shorter)]

    # Layer 3: token overlap (all seed subjects)
    tok = _token_overlap_display(seed_list, rec_list)
    if tok:
        return tok

    # Layer 4: head subjects — first two seed phrases only
    head = seed_list[:2]
    if head and head != seed_list:
        tok_head = _token_overlap_display(head, rec_list)
        if tok_head:
            return tok_head

    return None


def top_rec_subject_tags(rec_subjects_parsed: list[str], *, limit: int = 3) -> list[str]:
    """Pretty labels from recommended book subjects only (for rec-led fallback)."""
    if not rec_subjects_parsed:
        return []
    tags: list[str] = []
    for ph in rec_subjects_parsed:
        display = _display_from_normalized(ph.strip())
        if display and display not in tags:
            tags.append(display)
        if len(tags) >= limit:
            break
    return tags
