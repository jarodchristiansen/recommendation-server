# app/routes/recommendations.py
from fastapi import APIRouter, HTTPException
from app.utils.db import get_mongo_collection
from app.services.spotify_service import fetch_track_from_spotify
from app.services.recommendation_service import calculate_cosine_similarity, calculate_cosine_similarity_with_explanation, calculate_weighted_cosine_similarity
import os

router = APIRouter()

@router.get("/recommendations/cosine-similarity/{track_id}")
async def recommend_songs(track_id: str, token: str, top_n: int = 10):
    secret_token = os.getenv("SECRET_TOKEN")
    if token != secret_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    collection = get_mongo_collection()

    # Fetch the target song from MongoDB
    target_song = collection.find_one({"track_id": track_id})
    
    # Fetch from Spotify if not found
    if not target_song:
        try:
            target_song = fetch_track_from_spotify(track_id)
            collection.insert_one(target_song)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Track not found: {str(e)}")

    # Ensure necessary features exist
    required_features = ['danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']
    if not all(key in target_song and target_song[key] is not None for key in required_features):
        raise HTTPException(status_code=400, detail="Target song is missing necessary audio features")

    # Get all tracks with necessary features
    all_tracks = list(collection.find({key: {"$exists": True, "$ne": None} for key in required_features}, {
        "_id": 0, "track_id": 1, "track_name": 1, "artist_name": 1, "popularity": 1, **{key: 1 for key in required_features}
    }))

    # Define feature columns for similarity calculation
    feature_columns = ['popularity', 'danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']
    
    # Calculate recommendations with explanations
    recommended_tracks = calculate_cosine_similarity_with_explanation(
        target_song, all_tracks, feature_columns, top_n)

    return {
        "recommendations": recommended_tracks,
        "target_features": {key: target_song[key] for key in feature_columns},
    }

@router.get("/recommendations/weighted-cosine/{track_id}")
async def recommend_songs_with_weights(
    track_id: str,
    token: str,
    acousticness_weight: float = 1.0,
    danceability_weight: float = 1.0,
    energy_weight: float = 1.0,
    instrumentalness_weight: float = 1.0,
    liveness_weight: float = 1.0,
    loudness_weight: float = 1.0,
    speechiness_weight: float = 1.0,
    tempo_weight: float = 1.0,
    valence_weight: float = 1.0,
    popularity_weight: float = 1.0,
    top_n: int = 10
):
    secret_token = os.getenv("SECRET_TOKEN")
    if token != secret_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    collection = get_mongo_collection()

    # Fetch the target song from MongoDB
    target_song = collection.find_one({"track_id": track_id})
    
    if not target_song:
        try:
            target_song = fetch_track_from_spotify(track_id)
            collection.insert_one(target_song)
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Track not found: {str(e)}")

    # Ensure track has all the necessary audio features
    if not all(key in target_song for key in ['danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']):
        raise HTTPException(status_code=400, detail="Target song missing audio features.")

    # Fetch all tracks with necessary features from MongoDB
    all_tracks = list(collection.find({
        "danceability": {"$exists": True},
        "energy": {"$exists": True},
        "valence": {"$exists": True},
        "loudness": {"$exists": True},
        "key": {"$exists": True},
        "speechiness": {"$exists": True},
        "acousticness": {"$exists": True},
        "instrumentalness": {"$exists": True},
        "liveness": {"$exists": True},
        "tempo": {"$exists": True},
        "popularity": {"$exists": True}
    }, {
        "_id": 0, "track_id": 1, "track_name": 1, "artist_name": 1, "popularity": 1,
        "danceability": 1, "energy": 1, "valence": 1, "loudness": 1, "key": 1, "speechiness": 1, 
        "acousticness": 1, "instrumentalness": 1, "liveness": 1, "tempo": 1
    }))

    if len(all_tracks) == 0:
        raise HTTPException(status_code=404, detail="No tracks found with sufficient features")

    # Define feature columns and weights
    feature_columns = [
        'acousticness', 'danceability', 'energy', 'instrumentalness',
        'liveness', 'loudness', 'speechiness', 'tempo', 'valence', 'popularity'
    ]

    # Create a weights dictionary to pass into cosine similarity
    weights = {
        'acousticness': acousticness_weight,
        'danceability': danceability_weight,
        'energy': energy_weight,
        'instrumentalness': instrumentalness_weight,
        'liveness': liveness_weight,
        'loudness': loudness_weight,
        'speechiness': speechiness_weight,
        'tempo': tempo_weight,
        'valence': valence_weight,
        'popularity': popularity_weight
    }

    # Calculate recommendations using weighted cosine similarity
    recommended_tracks = calculate_weighted_cosine_similarity(target_song, all_tracks, feature_columns, top_n, weights)

    return {"recommendations": recommended_tracks}

# @router.get("/recommendations/weighted-cosine/{track_id}")
# async def recommend_songs_with_weights(
#     track_id: str,
#     token: str,
#     acousticness_weight: float = 1.0,
#     danceability_weight: float = 1.0,
#     energy_weight: float = 1.0,
#     instrumentalness_weight: float = 1.0,
#     liveness_weight: float = 1.0,
#     loudness_weight: float = 1.0,
#     speechiness_weight: float = 1.0,
#     tempo_weight: float = 1.0,
#     valence_weight: float = 1.0,
#     popularity_weight: float = 1.0,
#     top_n: int = 10
# ):
#     secret_token = os.getenv("SECRET_TOKEN")
#     if token != secret_token:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     collection = get_mongo_collection()

#     # Fetch the target song from MongoDB
#     target_song = collection.find_one({"track_id": track_id})
    
#     if not target_song:
#         try:
#             target_song = fetch_track_from_spotify(track_id)
#             collection.insert_one(target_song)
#         except Exception as e:
#             raise HTTPException(status_code=404, detail=f"Track not found: {str(e)}")

#     # Ensure track has all the necessary audio features
#     if not all(key in target_song for key in ['danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']):
#         raise HTTPException(status_code=400, detail="Target song missing audio features.")

#     # Feature columns and weights
#     feature_columns = [
#         'acousticness', 'danceability', 'energy', 'instrumentalness',
#         'liveness', 'loudness', 'speechiness', 'tempo', 'valence', 'popularity'
#     ]
#     weights = {
#         'acousticness': acousticness_weight,
#         'danceability': danceability_weight,
#         'energy': energy_weight,
#         'instrumentalness': instrumentalness_weight,
#         'liveness': liveness_weight,
#         'loudness': loudness_weight,
#         'speechiness': speechiness_weight,
#         'tempo': tempo_weight,
#         'valence': valence_weight,
#         'popularity': popularity_weight
#     }


#     # Fetch all tracks with necessary features from MongoDB
#     all_tracks = list(collection.find({
#         "danceability": {"$exists": True},
#         "energy": {"$exists": True},
#         "valence": {"$exists": True},
#         "loudness": {"$exists": True},
#         "key": {"$exists": True},
#         "speechiness": {"$exists": True},
#         "acousticness": {"$exists": True},
#         "instrumentalness": {"$exists": True},
#         "liveness": {"$exists": True},
#         "tempo": {"$exists": True},
#         "popularity": {"$exists": True}
#     }, {
#         "_id": 0, "track_id": 1, "track_name": 1, "artist_name": 1, "popularity": 1,
#         "danceability": 1, "energy": 1, "valence": 1, "loudness": 1, "key": 1, "speechiness": 1, 
#         "acousticness": 1, "instrumentalness": 1, "liveness": 1, "tempo": 1
#     }))

#     if len(all_tracks) == 0:
#         raise HTTPException(status_code=404, detail="No tracks found with sufficient features")


#     # Apply PCA to tracks and store the matrix (or load it)
#     reduced_features, _ = apply_pca_to_features(all_tracks, feature_columns)

#     # Precompute and store the similarity matrix (or load it)
#     similarity_matrix = precompute_similarity_matrix(reduced_features)

#     # Calculate weighted cosine similarity from the precomputed matrix
#     recommended_tracks = calculate_weighted_cosine_similarity_from_matrix(
#         target_song, all_tracks, similarity_matrix, top_n
#     )

#     return {"recommendations": recommended_tracks}
