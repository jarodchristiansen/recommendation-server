"""Unit tests for deterministic book explanations (A–C enhancements)."""

import pytest

from app.services.explanation_service import build_deterministic_explanation
from app.services.explanation_subject_signals import (
    find_shared_subject_labels,
    jaccard_overlap,
    parse_subjects_csv,
)


def test_jaccard_overlap():
    score, shared = jaccard_overlap(["a", "b"], ["b", "c"])
    assert score == 1 / 3
    assert shared == ["b"]


def test_exact_phrase_overlap_wins():
    shared = find_shared_subject_labels(
        ["Fantasy", "Magic"],
        parse_subjects_csv("Fantasy, Young adult"),
    )
    assert shared is not None
    assert "Fantasy" in shared


def test_alias_maps_sci_fi():
    shared = find_shared_subject_labels(
        ["Science fiction"],
        parse_subjects_csv("Sci-fi adventures, Space"),
    )
    assert shared is not None


def test_token_overlap_science_fiction_vs_csv():
    shared = find_shared_subject_labels(
        ["Science fiction"],
        parse_subjects_csv("Hard science, space exploration"),
    )
    assert shared is not None
    assert any("Science" in s for s in shared)


def test_build_thematic_prefers_exact_before_fuzzy():
    s = build_deterministic_explanation(
        seed_subjects=["Fantasy"],
        seed_author="X",
        rec={
            "author_name": "Y",
            "subjects": "Fantasy, Epics",
            "total_shelf_count": 0,
            "has_rating": False,
        },
    )
    assert "Fantasy" in s
    assert "thematic overlap" in s.lower() or "Shares thematic" in s


def test_high_rating_no_false_subject_overlap_claim():
    s = build_deterministic_explanation(
        seed_subjects=["Quantum physics"],
        seed_author="A",
        rec={
            "author_name": "B",
            "subjects": "Cooking, Baking",
            "total_shelf_count": 100,
            "has_rating": True,
            "avg_rating": 4.3,
        },
    )
    assert "4.3" in s
    assert "subject overlap" not in s.lower()


def test_thematic_branch_wins_when_subjects_align_even_if_highly_rated():
    s = build_deterministic_explanation(
        seed_subjects=["Fantasy"],
        seed_author="A",
        rec={
            "author_name": "B",
            "subjects": "Fantasy, Magic",
            "total_shelf_count": 100,
            "has_rating": True,
            "avg_rating": 4.5,
        },
    )
    assert "Fantasy" in s
    assert "thematic overlap" in s.lower() or "Shares thematic" in s


@pytest.mark.parametrize(
    "dist,needle",
    [
        (0.05, "Very close"),
        (0.15, "Strong"),
        (0.5, "Softer"),
    ],
)
def test_embedding_distance_buckets(dist, needle):
    s = build_deterministic_explanation(
        seed_subjects=["ZZZ_unlikely_token_xyz"],
        seed_author="A",
        rec={
            "author_name": "B",
            "subjects": "Dragons, Quests",
            "total_shelf_count": 500,
            "has_rating": False,
            "avg_rating": 0.0,
        },
        cosine_distance=dist,
    )
    assert needle in s
    assert "Dragons" in s or "Quests" in s


def test_rec_led_when_seed_empty_and_no_distance():
    s = build_deterministic_explanation(
        seed_subjects=[],
        seed_author="",
        rec={
            "author_name": "Someone",
            "subjects": "Mystery, Crime",
            "total_shelf_count": 500,
            "has_rating": False,
        },
        cosine_distance=None,
    )
    assert "Often tagged" in s
    assert "Mystery" in s or "Crime" in s


def test_generic_when_no_signals():
    s = build_deterministic_explanation(
        seed_subjects=[],
        seed_author="",
        rec={
            "author_name": "Someone",
            "subjects": "",
            "total_shelf_count": 0,
            "has_rating": False,
        },
        cosine_distance=None,
    )
    assert "semantic similarity" in s.lower()
