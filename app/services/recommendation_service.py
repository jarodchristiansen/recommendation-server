# app/services/recommendation_service.py
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA
import pickle
import os

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

def calculate_cosine_similarity_with_explanation(target_song, all_tracks, feature_columns, top_n=10):
    # Convert track features into NumPy arrays
    track_features = np.array([[track[col] for col in feature_columns] for track in all_tracks])
    target_features = np.array([[target_song[col] for col in feature_columns]])

    # Calculate cosine similarity between target and all tracks
    similarities = cosine_similarity(target_features, track_features)[0]

    # Get indices of the most similar tracks
    similar_indices = np.argsort(similarities)[::-1][1:top_n+1]

    # Prepare the recommended tracks with explanations
    recommended_tracks = []
    for idx in similar_indices:
        track = all_tracks[idx]
        similarity_score = similarities[idx]

        # Calculate the difference between target and recommended track for each feature
        feature_difference = {
            col: target_song[col] - track[col] for col in feature_columns
        }

        # Embed the similarity score and feature differences into each track object
        track_with_explanation = {
            **track,
            "similarity_score": similarity_score,
            "feature_difference": feature_difference
        }

        recommended_tracks.append(track_with_explanation)

    return recommended_tracks




def calculate_weighted_cosine_similarity(target_song, all_tracks, feature_columns, top_n=10, weights=None):
    if weights is None:
        weights = {feature: 1.0 for feature in feature_columns}  # Default all weights to 1

    # Extract feature values for the target song
    target_features = np.array([target_song[feature] * weights[feature] for feature in feature_columns])

    # List to store similarity results
    similarities = []

    # Compare the target song with all tracks
    for track in all_tracks:
        track_features = np.array([track[feature] * weights[feature] for feature in feature_columns])
        similarity_score = cosine_similarity([target_features], [track_features])[0][0]
        similarities.append((track, similarity_score))

    # Sort by similarity score and return the top N recommendations
    similarities.sort(key=lambda x: x[1], reverse=True)
    recommended_tracks = [track for track, _ in similarities[:top_n]]

    return recommended_tracks



def calculate_weighted_cosine_similarity_from_matrix(target_song, all_tracks, similarity_matrix, top_n=10):
    """
    Calculate cosine similarity using a precomputed similarity matrix.
    """
    # Find the index of the target song in the all_tracks list
    target_index = next(i for i, track in enumerate(all_tracks) if track['track_id'] == target_song['track_id'])
    
    # Get similarity scores for the target song from the matrix
    similarity_scores = similarity_matrix[target_index]
    
    # Get the top N most similar tracks
    sorted_indices = np.argsort(similarity_scores)[::-1]
    
    # Return the top N tracks
    recommended_tracks = [all_tracks[i] for i in sorted_indices[:top_n]]

    return recommended_tracks



def apply_pca_to_features(all_tracks, feature_columns, n_components=5, pca_filepath='pca_matrix.pkl'):
    """
    Apply PCA and save the matrix to a file if it doesn't exist.
    """
    if os.path.exists(pca_filepath):
        print("Loading PCA from file")
        with open(pca_filepath, 'rb') as f:
            pca, reduced_features = pickle.load(f)
    else:
        # Extract features from all tracks
        feature_matrix = np.array([[track[feature] for feature in feature_columns] for track in all_tracks])
        
        # Apply PCA
        pca = PCA(n_components=n_components)
        reduced_features = pca.fit_transform(feature_matrix)
        
        # Save the PCA and reduced features to a file
        with open(pca_filepath, 'wb') as f:
            pickle.dump((pca, reduced_features), f)
    
    return reduced_features, pca


def precompute_similarity_matrix(reduced_features, similarity_filepath='similarity_matrix.pkl'):
    """
    Precompute and store the similarity matrix as a local file.
    """
    if os.path.exists(similarity_filepath):
        print("Loading similarity matrix from file")
        with open(similarity_filepath, 'rb') as f:
            similarity_matrix = pickle.load(f)
    else:
        # Compute similarity matrix
        similarity_matrix = cosine_similarity(reduced_features)
        
        # Save to a file
        with open(similarity_filepath, 'wb') as f:
            pickle.dump(similarity_matrix, f)
    
    return similarity_matrix
