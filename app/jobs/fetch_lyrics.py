import requests
import pymongo
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

from services.spotify_service import get_spotify_client
from utils.db import get_mongo_collection
import re
import bleach


def fetch_lyrics_ovh(artist_name, song_title):
    # Set up MongoDB connection
    collection = get_mongo_collection()

    # Find records missing images, limit to MAX_REQUESTS at a time
    missing_lyrics = collection.find({"lryics": {"$exists": False}}).limit(2000)

    exceptions = 0

    # Make a for loop to fetch lyrics for each track missing them from db query
    for track in missing_lyrics:
        track_id = track['track_id']
        artist_name = track['artist_name']
        song_title = track['track_name']


        if exceptions >= 10:
            print("Too many exceptions, stopping for now.")
            break

        try:
            lyrics = fetch_lyrics(artist_name, song_title)
            if lyrics:
                collection.update_one({"track_id": track_id}, {"$set": {"lyrics": lyrics}})
                print(f"Updated lyrics for track {track_id}")
        except Exception as e:
            print(f"Error fetching lyrics for track {track_id}: {str(e)}")
            exceptions += 1




def fetch_lyrics(artist_name, song_title):
    base_url = f"https://api.lyrics.ovh/v1/{artist_name}/{song_title}"
    print(artist_name, song_title, 'Track FOR LYRICS REQUEST')
    response = requests.get(base_url)
    print(response.status_code, 'STATUS CODE FROM LRYICS REQUEST')
    if response.status_code == 200:
        data = response.json()
        lyrics = data.get("lyrics", "No lyrics found.")
        processed_lyrics = process_lyrics(lyrics)
        return processed_lyrics
    else:
        return "No lyrics found or too many requests."


def format_lyrics(lyrics_text):
    # Replace line breaks with <br> for HTML formatting
    return lyrics_text.replace("\r\n", "<br>").replace("\n", "<br>")

def clean_lyrics(lyrics_text):
    # Remove excess line breaks but keep paragraph breaks
    lyrics_text = re.sub(r'(\<br\>)+', '<br><br>', lyrics_text)
    return lyrics_text.strip()

def sanitize_lyrics(lyrics_text):
    # Sanitize to allow only <br> tags
    allowed_tags = ['br']
    return bleach.clean(lyrics_text, tags=allowed_tags)

def process_lyrics(lyrics_text):
    formatted = format_lyrics(lyrics_text)
    cleaned = clean_lyrics(formatted)
    sanitized = sanitize_lyrics(cleaned)
    return sanitized