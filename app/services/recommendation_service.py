# app/services/recommendation_service.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def calculate_cosine_similarity(target_song, all_tracks, feature_columns, top_n=10):
    # Convert track features into NumPy arrays for similarity calculation
    track_features = np.array([[track[col] for col in feature_columns] for track in all_tracks])
    target_features = np.array([[target_song[col] for col in feature_columns]])

    # Calculate cosine similarity between target and all tracks
    similarities = cosine_similarity(target_features, track_features)[0]

    # Get top_n most similar songs
    similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
    recommended_tracks = [all_tracks[i] for i in similar_indices]

    return recommended_tracks
