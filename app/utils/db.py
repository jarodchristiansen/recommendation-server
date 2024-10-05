# app/utils/db.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def get_mongo_collection():
    MONGO_URL = os.getenv("MONGO_URL")
    client = MongoClient(MONGO_URL)
    db = client.Tracks
    collection = db['tracks_with_features']
    return collection
