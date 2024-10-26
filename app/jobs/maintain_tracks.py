# import pymongo
# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials
# import os

# # Set up MongoDB connection
# client = pymongo.MongoClient(os.getenv('MONGO_URL'))
# db = client.Tracks
# collection = db['tracks_with_features']

# # Set up Spotify client
# spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
#     client_id=os.getenv("SPOTIFY_CLIENT_ID"),
#     client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
# ))

# # Spotify's API rate limits
# MAX_REQUESTS = 1000  # Set a limit of 1000 requests per run
# REQUEST_COUNT = 0  # Counter for how many requests have been made

# def update_missing_images():
#     global REQUEST_COUNT
    
#     # Find records missing images, limit to MAX_REQUESTS at a time
#     missing_images = collection.find({"image_url": {"$exists": False}}).limit(MAX_REQUESTS)

#     # Process missing album images
#     for track in missing_images:
#         if REQUEST_COUNT >= MAX_REQUESTS:
#             print(f"Reached the request limit of {MAX_REQUESTS}, stopping for now.")
#             break  # Stop processing if we hit the max number of requests

#         track_id = track['track_id']

#         try:
#             spotify_track = spotify.track(track_id)
#             image_url = spotify_track['album']['images'][0]['url'] if spotify_track['album']['images'] else None
#             if image_url:
#                 collection.update_one({"track_id": track_id}, {"$set": {"image_url": image_url}})
#                 print(f"Updated image for track {track_id}")
#             REQUEST_COUNT += 1  # Increment request count
#         except spotipy.SpotifyException as e:
#             # If we hit the rate limit, exit early and stop processing
#             print(f"Spotify API error: {e}")
#             break  # Exit the loop if rate-limited

#     print(f"Completed processing {REQUEST_COUNT} tracks this run.")

# # Execute the job (run this periodically, e.g., with a cron job)
# update_missing_images()


import pymongo
import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
import os

# Set up MongoDB connection
client = pymongo.MongoClient(os.getenv('MONGO_URL'))
db = client.Tracks
collection = db['tracks_with_features']

# Set up Spotify client
spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

# Spotify's API rate limits
MAX_REQUESTS = 2500
REQUEST_COUNT = 0  # Counter for how many requests have been made
MAX_RETRIES = 2  # Max retries in case of rate limiting or errors
BACKOFF_FACTOR = 2  # Exponential backoff factor for retries

def fetch_track_with_backoff(track_id, retries=MAX_RETRIES):
    """Fetch a track from Spotify API with exponential backoff in case of rate limiting."""
    delay = 1
    for attempt in range(retries):
        try:
            spotify_track = spotify.track(track_id)
            return spotify_track
        except SpotifyException as e:
            if "status" in e.msg and e.msg["status"] == 429:  # Rate limit error
                print(f"Rate limited on attempt {attempt+1} for track {track_id}. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= BACKOFF_FACTOR  # Increase delay exponentially
            else:
                print(f"Error fetching track {track_id}: {e}")
                break  # Stop retrying on non-rate-limit errors
    return None

def update_missing_images():
    global REQUEST_COUNT
    
    # Find records missing images, limit to MAX_REQUESTS at a time
    missing_images = collection.find({"image_url": {"$exists": False}}).limit(MAX_REQUESTS)

    # Process missing album images
    for track in missing_images:
        if REQUEST_COUNT >= MAX_REQUESTS:
            print(f"Reached the request limit of {MAX_REQUESTS}, stopping for now.")
            break

        track_id = track['track_id']
        time.sleep(3)
        spotify_track = fetch_track_with_backoff(track_id)

        if spotify_track:
            image_url = spotify_track['album']['images'][0]['url'] if spotify_track['album']['images'] else None
            if image_url:
                collection.update_one({"track_id": track_id}, {"$set": {"image_url": image_url}})
                print(f"Updated image for track {track_id}")
            REQUEST_COUNT += 1  # Increment request count
        else:
            print(f"Failed to update image for track {track_id} after retries.")

    print(f"Completed processing {REQUEST_COUNT} tracks this run.")

# Execute the job
update_missing_images()
