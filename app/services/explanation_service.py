"""
Deterministic explanation generation for book recommendations.

Precedence:
1. Same author as seed
2. Thematic overlap — layered subject signals (exact → alias → token → head-subject tokens)
3. High shelf count
4. High average rating (wording does not claim subject overlap unless step 2 matched)
5. Tier-1 embedding strength (from cosine distance) combined with rec-led subject tags,
   then rec-led tags alone, then embedding-only, then generic fallback

No LLM. See explanation_subject_signals.py and explanation_templates.py.
"""

from __future__ import annotations

from app.services import explanation_templates as T
from app.services.explanation_subject_signals import (
    find_shared_subject_labels,
    parse_subjects_csv,
    top_rec_subject_tags,
)

# Zilliz/Milvus COSINE metric: lower distance = closer vectors (≈ 1 − cosine similarity).
_TIGHT_DISTANCE = 0.10
_STRONG_DISTANCE = 0.22


def _strength_sentence(cosine_distance: float | None) -> str | None:
    if cosine_distance is None:
        return None
    d = float(cosine_distance)
    if d <= _TIGHT_DISTANCE:
        return T.embedding_tight()
    if d <= _STRONG_DISTANCE:
        return T.embedding_strong()
    return T.embedding_soft()


def build_deterministic_explanation(
    *,
    seed_subjects: list[str],
    seed_author: str,
    rec: dict,
    cosine_distance: float | None = None,
) -> str:
    """
    Human-readable reason this `rec` appeared for the given seed metadata.

    cosine_distance: search hit distance for Tier-1 vector search only; use None for Tier-3 queries.
    """
    rec_author = (rec.get("author_name") or "").strip()
    if rec_author and seed_author and rec_author.lower() == seed_author.strip().lower():
        return T.same_author(rec_author)

    rec_subjects = parse_subjects_csv(rec.get("subjects") or "")
    shared = find_shared_subject_labels(seed_subjects, rec_subjects)
    had_subject_overlap = shared is not None

    if shared:
        return T.thematic_overlap(shared)

    shelf = int(rec.get("total_shelf_count") or 0)
    if shelf > 10_000:
        return T.shelf_popular(shelf)

    avg = rec.get("avg_rating")
    if rec.get("has_rating") and (avg or 0) >= 4.0:
        return T.highly_rated(float(avg), had_subject_overlap=had_subject_overlap)

    strength = _strength_sentence(cosine_distance)
    tags = top_rec_subject_tags(rec_subjects, limit=3)

    if strength and tags:
        return T.embedding_plus_tags(strength, tags)
    if tags:
        return T.rec_lane_from_tags(tags)
    if strength:
        return T.embedding_no_tags(strength)
    return T.generic_semantic()


# Re-export for backwards compatibility with imports from this module.
from app.services.explanation_subject_signals import jaccard_overlap  # noqa: F401
