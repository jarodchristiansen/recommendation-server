# Open Library API client for book metadata. Replaces Spotify for the books migration.
# See MIGRATION_AND_ARCHITECTURE.md section 9. Identify with User-Agent + contact for rate limits.

import os
import re
import time
import requests
from fastapi import HTTPException

BASE_URL = "https://openlibrary.org"
COVERS_BASE = "https://covers.openlibrary.org/b/id"
# Rate limit: with User-Agent + contact, ~3 req/s. Be conservative.
_REQUEST_DELAY_SEC = 0.4


def _headers():
    user_agent = os.getenv("OPEN_LIBRARY_USER_AGENT", "RecommendationApp/1.0")
    contact = os.getenv("OPEN_LIBRARY_CONTACT_EMAIL", "")
    if contact:
        user_agent = f"{user_agent} ({contact})"
    return {"User-Agent": user_agent, "Accept": "application/json"}


def _normalize_work_id(work_id: str) -> str:
    """Return OL-style id e.g. OL45804W. Accepts OL45804W or /works/OL45804W."""
    s = work_id.strip()
    m = re.search(r"OL\d+W", s, re.IGNORECASE)
    return m.group(0).upper() if m else s


def _work_key(work_id: str) -> str:
    n = _normalize_work_id(work_id)
    return f"/works/{n}" if not n.startswith("/") else n


def _fetch_json(url: str) -> dict:
    time.sleep(_REQUEST_DELAY_SEC)
    r = requests.get(url, headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _author_name(author_key: str) -> str:
    """Fetch author display name. author_key e.g. /authors/OL34184A."""
    if not author_key or not author_key.startswith("/authors/"):
        return "Unknown"
    url = f"{BASE_URL}{author_key}.json"
    try:
        data = _fetch_json(url)
        return data.get("name") or data.get("personal_name") or "Unknown"
    except Exception:
        return "Unknown"


def fetch_work(work_id: str) -> dict:
    """
    Fetch a work by ID from Open Library and return a document suitable for
    Books.books_with_metadata. On failure raises HTTPException(404).
    """
    key = _work_key(work_id)
    url = f"{BASE_URL}{key}.json"
    try:
        data = _fetch_json(url)
    except requests.RequestException as e:
        raise HTTPException(status_code=404, detail=f"Work not found: {str(e)}")

    # Extract fields
    work_id_norm = _normalize_work_id(work_id)
    title = data.get("title") or "Unknown"
    authors = data.get("authors") or []
    author_key = authors[0]["author"]["key"] if authors else None
    author_name_str = _author_name(author_key) if author_key else "Unknown"
    subjects = data.get("subjects") or []
    covers = data.get("covers") or []

    cover_i = None
    if covers:
        # Prefer first positive cover ID (Open Library uses -1 for placeholder)
        for c in covers:
            if isinstance(c, int) and c > 0:
                cover_i = c
                break
        if cover_i is None and isinstance(covers[0], int):
            cover_i = covers[0]

    cover_url = f"{COVERS_BASE}/{cover_i}-M.jpg" if cover_i and cover_i > 0 else None

    # Numeric features for cosine similarity
    subject_count = len(subjects)
    author_count = len(authors)
    cover_count = len([c for c in covers if isinstance(c, int) and c > 0]) or (1 if cover_i else 0)

    # Enrich with first_publish_year and ratings from Search API (one extra call)
    first_publish_year = 0
    ratings_average = 0.0
    try:
        # Search by work ID so we get this work in results (key in response is e.g. /works/OL45804W)
        search_url = f"{BASE_URL}/search.json?q={work_id_norm}&limit=5&fields=key,first_publish_year,ratings_average"
        time.sleep(_REQUEST_DELAY_SEC)
        r = requests.get(search_url, headers=_headers(), timeout=15)
        if r.ok:
            search_data = r.json()
            for hit in (search_data.get("docs") or []):
                if hit.get("key") == key:
                    first_publish_year = int(hit.get("first_publish_year") or 0) or 0
                    ratings_average = float(hit.get("ratings_average") or 0) or 0.0
                    break
    except Exception:
        pass

    doc = {
        "work_id": work_id_norm,
        "title": title,
        "author_name": author_name_str,
        "author_count": author_count,
        "subject_count": subject_count,
        "cover_count": cover_count,
        "cover_i": cover_i,
        "cover_url": cover_url,
        "subjects": subjects[:20],
        "first_publish_year": first_publish_year,
        "ratings_average": ratings_average,
    }
    return doc
