# Tests for deprecated Spotify service stub.
# Migration: Spotify removed; stub raises 501. See MIGRATION_CHECKPOINT.md.

from app.services.spotify_service import fetch_track_from_spotify, get_spotify_client
from fastapi import HTTPException
import pytest


def test_fetch_track_from_spotify_raises_deprecated():
    with pytest.raises(HTTPException) as excinfo:
        fetch_track_from_spotify("any_id")
    assert excinfo.value.status_code == 501
    assert "Spotify" in str(excinfo.value.detail)
    assert "Open Library" in str(excinfo.value.detail)


def test_get_spotify_client_raises_deprecated():
    with pytest.raises(HTTPException) as excinfo:
        get_spotify_client()
    assert excinfo.value.status_code == 501
    assert "Spotify" in str(excinfo.value.detail)
