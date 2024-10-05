
# import os
# from pymongo import MongoClient
# from fastapi import FastAPI, HTTPException
# from dotenv import load_dotenv  # To load environment variables from a .env file
# from bson import ObjectId  # For handling MongoDB ObjectIds
# from typing import Optional
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity

# # # Load environment variables
# load_dotenv()

# # Initialize FastAPI app
# app = FastAPI()

# # Connect to MongoDB
# MONGO_URL = os.getenv("MONGO_URL")
# client = MongoClient(MONGO_URL)
# db = client.Tracks
# collection = db['tracks_with_features']

# # Root endpoint
# @app.get("/")
# async def root():
#     return {"message": "Hello World"}

# # Fetch track from MongoDB by track_id
# @app.get("/track/{track_id}")
# def get_track(track_id: str):
#     track = collection.find_one({"track_id": track_id})
#     if not track:
#         raise HTTPException(status_code=404, detail="Track not found")
#     return track

# @app.get("/recommendations/cosine-similarity/{track_id}")
# def recommend_songs(track_id: str, token: str, top_n: int = 10):
    
#     secret_token = os.getenv("SECRET_TOKEN")
#     if token != secret_token:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     # Fetch the target song from the MongoDB collection
#     target_song = collection.find_one({"track_id": track_id})
#     if not target_song:
#         raise HTTPException(status_code=404, detail="Track not found")
    
#     # Get all tracks with features
#     all_tracks = list(collection.find({}, {"_id": 0, "track_id": 1, "track_name": 1, "artist_name": 1, "popularity": 1,
#                                            "danceability": 1, "energy": 1, "valence": 1,
#                                            "loudness": 1, "key": 1, "speechiness": 1}))
    
#     # Convert the track features into a NumPy array for similarity calculation
#     feature_columns = ['popularity', 'danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']
#     track_features = np.array([[track[col] for col in feature_columns] for track in all_tracks])
    
#     # Target song feature vector
#     target_features = np.array([[target_song[col] for col in feature_columns]])

#     # Calculate cosine similarity between target song and all tracks
#     similarities = cosine_similarity(target_features, track_features)[0]
    
#     # Get indices of top_n most similar songs
#     similar_indices = np.argsort(similarities)[::-1][1:top_n+1]
#     recommended_tracks = [all_tracks[i] for i in similar_indices]

#     return {"recommendations": recommended_tracks}


# app/main.py
from fastapi import FastAPI
from app.routes import recommendations

app = FastAPI()

# Include recommendations routes
app.include_router(recommendations.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
