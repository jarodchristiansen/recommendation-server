# DEPRECATED: Spotify service removed for migration to Open Library (books).
# See MIGRATION_AND_ARCHITECTURE.md and MIGRATION_CHECKPOINT.md.
#
# REPLACEMENT PLAN:
# - Add app/services/open_library_service.py (or similar) that:
#   - Fetches work/edition by ID from Open Library (e.g. GET works/{workId}.json).
#   - Maps response to a stored document shape for the Books collection.
#   - Uses User-Agent and contact email for rate limits (see doc section 9).
# - Recommendation route will call this service when target book is missing in MongoDB,
#   then run similarity on the new book feature set (subjects, author, year, etc.).

from fastapi import HTTPException


def get_spotify_client():
    """Deprecated. Do not use. Replaced by Open Library client."""
    raise HTTPException(
        status_code=501,
        detail="Spotify integration removed. Migration to Open Library in progress.",
    )


def fetch_track_from_spotify(track_id: str):
    """Deprecated. Do not use. Replaced by Open Library fetch_work/fetch_edition."""
    raise HTTPException(
        status_code=501,
        detail="Spotify integration removed. Migration to Open Library in progress.",
    )
