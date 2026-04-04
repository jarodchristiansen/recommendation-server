"""Milvus / Zilliz search hit normalization (empty entity + flat output_fields)."""

from app.utils.milvus_search_hits import (
    normalize_open_library_work_id,
    same_open_library_work,
    search_hit_entity_dict,
)


def test_empty_entity_uses_top_level_output_fields():
    """Regression: empty entity {} must not hide flat scalars (Zilliz / pymilvus variants)."""
    hit = {
        "id": 1,
        "distance": 0.12,
        "entity": {},
        "work_key": "/works/OL100W",
        "title": "Test Book",
        "author_name": "A",
        "subjects": "Fantasy, Magic",
    }
    entity = search_hit_entity_dict(hit)
    assert entity is not None
    assert entity["work_key"] == "/works/OL100W"
    assert entity["title"] == "Test Book"
    assert entity["subjects"] == "Fantasy, Magic"


def test_nested_entity_prefers_inner_over_flat():
    hit = {
        "id": 2,
        "distance": 0.2,
        "entity": {"work_key": "/works/OL200W", "title": "Inner Title"},
    }
    entity = search_hit_entity_dict(hit)
    assert entity["work_key"] == "/works/OL200W"
    assert entity["title"] == "Inner Title"


def test_flat_hit_without_entity_key():
    hit = {
        "id": 3,
        "distance": 0.3,
        "work_key": "OL300W",
        "title": "Flat",
    }
    entity = search_hit_entity_dict(hit)
    assert entity["work_key"] == "OL300W"


def test_same_open_library_work_prefix_variants():
    assert same_open_library_work("/works/OL45804W", "OL45804W") is True
    assert same_open_library_work("ol45804w", "/works/OL45804W") is True
    assert same_open_library_work("/works/OL1W", "/works/OL2W") is False


def test_normalize_open_library_work_id():
    assert normalize_open_library_work_id("/works/OL1W") == "OL1W"
    assert normalize_open_library_work_id("ol999w") == "OL999W"
