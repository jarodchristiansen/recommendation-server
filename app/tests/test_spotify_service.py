from unittest.mock import patch, MagicMock
from app.services.spotify_service import fetch_track_from_spotify, get_spotify_client
from fastapi import HTTPException
import pytest

def test_fetch_track_from_spotify_success():
    # Mock the Spotify API client and its response
    mock_track_response = {
        "name": "Test Song",
        "artists": [{"name": "Test Artist"}],
        "popularity": 85,
    }
    mock_audio_features_response = [{
        "danceability": 0.8,
        "energy": 0.7,
        "valence": 0.5,
        "loudness": -5.5,
        "key": 5,
        "speechiness": 0.05,
        "mode": 1,
        "acousticness": 0.3,
        "instrumentalness": 0.0,
        "liveness": 0.1,
        "tempo": 120,
        "duration_ms": 180000,
        "time_signature": 4,
        "track_href": "https://api.spotify.com/v1/tracks/test_track_id"
    }]

    with patch("spotipy.Spotify.track", return_value=mock_track_response) as mock_track, \
         patch("spotipy.Spotify.audio_features", return_value=mock_audio_features_response) as mock_audio_features:
        
        result = fetch_track_from_spotify("test_track_id")
        
        # Assert the structure of the returned data
        assert result["track_id"] == "test_track_id"
        assert result["track_name"] == "Test Song"
        assert result["artist_name"] == "Test Artist"
        assert result["danceability"] == 0.8
        assert result["tempo"] == 120

        # Assert that the mocks were called correctly
        mock_track.assert_called_once_with("test_track_id")
        mock_audio_features.assert_called_once_with("test_track_id")


def test_fetch_track_from_spotify_not_found():
    # Simulate the Spotify client raising an exception for a non-existent track
    with patch("spotipy.Spotify.track", side_effect=Exception("Not Found")) as mock_track, \
         patch("spotipy.Spotify.audio_features", return_value=[None]) as mock_audio_features:

        with pytest.raises(HTTPException) as excinfo:
            fetch_track_from_spotify("non_existent_track_id")
        
        assert excinfo.value.status_code == 404
        assert "Track not found" in str(excinfo.value.detail)

        # Assert that the track request was attempted even though it failed
        mock_track.assert_called_once_with("non_existent_track_id")

