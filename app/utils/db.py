# app/utils/db.py
# MongoDB is used for user data only (future: profiles, reading history, saved books).
# Book recommendations are served from Zilliz (POST /recommend). Do not use MongoDB for book catalog or recommendations.
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()


def get_mongo_collection():
    """Legacy: Tracks collection (Spotify-era). Used only by GET /recommendations/cosine-similarity/{track_id}."""
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise RuntimeError("MONGO_URL is required for track recommendations")
    client = MongoClient(MONGO_URL)
    db = client.Tracks
    collection = db["tracks_with_features"]
    return collection


def get_books_collection():
    """Reserved for future user data (e.g. saved books, reading list, profiles). Not used by recommendation flow; book recommendations use Zilliz (POST /recommend)."""
    MONGO_URL = os.getenv("MONGO_URL")
    if not MONGO_URL:
        raise RuntimeError("MONGO_URL is required for user data")
    client = MongoClient(MONGO_URL)
    db = client.Books
    collection = db["books_with_metadata"]
    return collection
