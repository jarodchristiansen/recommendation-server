# app/services/spotify_service.py
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

def get_spotify_client():
    spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
    ))
    return spotify

def fetch_track_from_spotify(track_id: str):
    spotify = get_spotify_client()

    # Fetch the track and audio features
    track = spotify.track(track_id)
    audio_features = spotify.audio_features(track_id)

    # Check if audio_features contains data
    if not audio_features or audio_features[0] is None:
        raise HTTPException(status_code=404, detail="Audio features not found")

    # Extract the first item from the audio features list
    audio_features = audio_features[0]

    # Print for debugging
    print(audio_features, track)

    # Extract relevant features
    track_data = {
        "track_id": track_id,
        "track_name": track["name"],
        "artist_name": track["artists"][0]["name"],
        "popularity": track["popularity"],
        "danceability": audio_features["danceability"],
        "energy": audio_features["energy"],
        "valence": audio_features["valence"],
        "loudness": audio_features["loudness"],
        "key": audio_features["key"],
        "speechiness": audio_features["speechiness"],
        "mode": audio_features["mode"],
        "acousticness": audio_features["acousticness"],
        "instrumentalness": audio_features["instrumentalness"],
        "liveness": audio_features["liveness"],
        "tempo": audio_features["tempo"],
        "duration_ms": audio_features["duration_ms"],
        "time_signature": audio_features["time_signature"],
        "track_href": audio_features["track_href"]
    }
    
    # Print for debugging
    print(track_data, 'TRACK DATA IN SPOTIFY FETCHER')

    return track_data