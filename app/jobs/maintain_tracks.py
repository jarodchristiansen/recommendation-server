import pymongo
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
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
MAX_REQUESTS = 1000  # Set a limit of 1000 requests per run
REQUEST_COUNT = 0  # Counter for how many requests have been made

def update_missing_images():
    global REQUEST_COUNT
    
    # Find records missing images, limit to MAX_REQUESTS at a time
    missing_images = collection.find({"image_url": {"$exists": False}}).limit(MAX_REQUESTS)

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
                print(f"Updated image for track {track_id}")
            REQUEST_COUNT += 1  # Increment request count
        except spotipy.SpotifyException as e:
            # If we hit the rate limit, exit early and stop processing
            print(f"Spotify API error: {e}")
            break  # Exit the loop if rate-limited

    print(f"Completed processing {REQUEST_COUNT} tracks this run.")

# Execute the job (run this periodically, e.g., with a cron job)
update_missing_images()
