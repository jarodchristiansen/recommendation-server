# from fastapi.testclient import TestClient
# import os

# # relies on conftest.py import to manage main.py being outside /app
# from main import app

# client = TestClient(app)

# def test_recommendations_authentication():
#     secret_token = os.getenv("SECRET_TOKEN")

#     response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": "test_token"})
#     assert response.status_code == 401

#     response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": secret_token})
#     assert response.status_code == 200
#     assert 'recommendations' in response.json()

# def test_recommendations_authentication():
#     secret_token = os.getenv("SECRET_TOKEN")

#     response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": secret_token})
#     assert response.status_code == 200
#     assert 'target_features' in response.json()    


from fastapi.testclient import TestClient
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.services.recommendation_service import (
    calculate_cosine_similarity,
    calculate_cosine_similarity_with_explanation
)


# Import app from main using conftest for the test environment
from main import app

client = TestClient(app)


# Sample test data for tracks
dummy_tracks = [
    {
        "track_id": "1",
        "track_name": "Track A",
        "artist_name": "Artist A",
        "popularity": 80,
        "danceability": 0.8,
        "energy": 0.7,
        "valence": 0.6,
        "loudness": -5.0,
        "key": 5,
        "speechiness": 0.05
    },
    {
        "track_id": "2",
        "track_name": "Track B",
        "artist_name": "Artist B",
        "popularity": 70,
        "danceability": 0.6,
        "energy": 0.8,
        "valence": 0.4,
        "loudness": -6.0,
        "key": 3,
        "speechiness": 0.1
    },
    {
        "track_id": "3",
        "track_name": "Track C",
        "artist_name": "Artist C",
        "popularity": 60,
        "danceability": 0.5,
        "energy": 0.9,
        "valence": 0.3,
        "loudness": -4.0,
        "key": 4,
        "speechiness": 0.07
    }
]

# Sample target track
target_track = {
    "track_id": "target",
    "track_name": "Target Track",
    "artist_name": "Target Artist",
    "popularity": 75,
    "danceability": 0.7,
    "energy": 0.75,
    "valence": 0.5,
    "loudness": -5.5,
    "key": 4,
    "speechiness": 0.06
}

# Define feature columns used in recommendations
feature_columns = ['popularity', 'danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']


def test_recommendations_authentication():
    # Test for valid and invalid tokens
    secret_token = os.getenv("SECRET_TOKEN")
    invalid_token = "invalid_token"

    # Invalid token should return 401
    response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": invalid_token})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token"}

    # Valid token should return 200
    response = client.get("/recommendations/cosine-similarity/3wzAXBZ6mhuYEzf2IJAbDc", params={"token": secret_token})
    assert response.status_code == 200
    assert 'recommendations' in response.json()
    assert 'target_features' in response.json()

def test_recommendations_missing_track():
    # Test for a track that is not in the database
    secret_token = os.getenv("SECRET_TOKEN")
    non_existent_track_id = "non_existent_track"

    response = client.get(f"/recommendations/cosine-similarity/{non_existent_track_id}", params={"token": secret_token})
    assert response.status_code == 404
    assert "Track not found" in response.json()['detail']

def test_recommendations_missing_features():
    # Test when a track is missing features (simulate using a mock)
    secret_token = os.getenv("SECRET_TOKEN")

    # Add a track with missing features for testing (mocking or pre-adding to your test database)
    track_with_missing_features = {
        "track_id": "missing_features_track",
        "track_name": "Test Track",
        "artist_name": "Test Artist"
    }
    # This would add the track directly if you are using a real MongoDB test environment
    client.post("/test/add_track", json=track_with_missing_features)

    # Try to get recommendations for the track with missing features
    response = client.get("/recommendations/cosine-similarity/missing_features_track", params={"token": secret_token})
    assert response.status_code == 404


def test_calculate_cosine_similarity():
    top_n = 2
    recommendations = calculate_cosine_similarity(target_track, dummy_tracks, feature_columns, top_n)

    # Assert that the correct number of recommendations is returned
    assert len(recommendations) == top_n

    # Assert that recommendations are sorted by similarity (descending order)
    similarities = [
        cosine_similarity(
            np.array([[target_track[col] for col in feature_columns]]),
            np.array([[track[col] for col in feature_columns]])
        )[0][0]
        for track in recommendations
    ]
    assert similarities == sorted(similarities, reverse=True)


def test_calculate_cosine_similarity_with_explanation():
    top_n = 2
    recommendations_with_explanations = calculate_cosine_similarity_with_explanation(
        target_track, dummy_tracks, feature_columns, top_n
    )

    # Assert that the correct number of recommendations is returned
    assert len(recommendations_with_explanations) == top_n

    # Check that each recommendation has a similarity score and feature differences
    for recommendation in recommendations_with_explanations:
        assert 'similarity_score' in recommendation
        assert isinstance(recommendation['similarity_score'], float)

        assert 'feature_difference' in recommendation
        feature_diff = recommendation['feature_difference']
        assert isinstance(feature_diff, dict)

        # Ensure that the feature_difference keys match the feature columns
        for col in feature_columns:
            assert col in feature_diff