# app/routes/recommendations.py
from fastapi import APIRouter, HTTPException
from app.utils.db import get_mongo_collection
from app.services.spotify_service import fetch_track_from_spotify
from app.services.recommendation_service import calculate_cosine_similarity
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
    
    # If the track is not in the DB, fetch from Spotify and insert it
    if not target_song:
        try:
            target_song = fetch_track_from_spotify(track_id)
            print(target_song, 'TARGET SONG IN RECOMMENDATION')
            collection.insert_one(target_song)  # Insert track into MongoDB
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Track not found: {str(e)}")
    
    # Get all tracks from MongoDB with necessary features
    all_tracks = list(collection.find({}, {"_id": 0, "track_id": 1, "track_name": 1, "artist_name": 1, "popularity": 1,
                                           "danceability": 1, "energy": 1, "valence": 1,
                                           "loudness": 1, "key": 1, "speechiness": 1}))
    
    # Define feature columns for similarity calculation
    feature_columns = ['popularity', 'danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']
    
    # Calculate recommendations using cosine similarity
    recommended_tracks = calculate_cosine_similarity(target_song, all_tracks, feature_columns, top_n)

    return {"recommendations": recommended_tracks}
