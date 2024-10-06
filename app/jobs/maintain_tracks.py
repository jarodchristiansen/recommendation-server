import time
import pymongo
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
# from utils.db import get_mongo_collection
# from app.utils.db import get_mongo_collection
import os

# # Set up MongoDB connection
client = pymongo.MongoClient(os.getenv('MONGO_URL'))
db = client.Tracks
collection = db['tracks_with_features']

# Set up Spotify client
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

# collection = get_mongo_collection()

# Spotify's API rate limits
MAX_REQUESTS = 1500  # Set a limit of 1000 requests per run
REQUEST_COUNT = 0  # Counter for how many requests have been made

def update_missing_data():
    global REQUEST_COUNT
    
    # Find records missing audio_features or images, limit to 1000 at a time
    missing_features = collection.find({"danceability": {"$exists": False}}).limit(MAX_REQUESTS)
    missing_images = collection.find({"image_url": {"$exists": False}}).limit(MAX_REQUESTS)

    # Process missing audio features
    for track in missing_features:
        if REQUEST_COUNT >= MAX_REQUESTS:
            print(f"Reached the request limit of {MAX_REQUESTS}, stopping for now.")
            break  # Stop processing if we hit the max number of requests

        track_id = track['track_id']

        try:
            audio_features = spotify.audio_features(track_id)
            if audio_features:
                collection.update_one({"track_id": track_id}, {"$set": {"audio_features": audio_features[0]}})
            REQUEST_COUNT += 1  # Increment request count
        except spotipy.SpotifyException as e:
            # If we hit the rate limit, exit early and stop processing
            print(f"Spotify API error: {e}")
            break  # Exit the loop to avoid being rate-limited further

    # Process missing album images
    for track in missing_images:
        if REQUEST_COUNT >= MAX_REQUESTS:
            print(f"Reached the request limit of {MAX_REQUESTS}, stopping for now.")
            break  # Stop processing if we hit the max number of requests

        track_id = track['track_id']

        try:
            spotify_track = spotify.track(track_id)
            image_url = spotify_track['album']['images'][0]['url'] if spotify_track['album']['images'] else None
            if image_url:
                collection.update_one({"track_id": track_id}, {"$set": {"image_url": image_url}})
            REQUEST_COUNT += 1  # Increment request count
        except spotipy.SpotifyException as e:
            print(f"Spotify API error: {e}")
            break  # Exit the loop if rate-limited

    print(f"Completed processing {REQUEST_COUNT} tracks this run.")

# Execute the job (run this periodically, e.g., with a cron job)
update_missing_data()
