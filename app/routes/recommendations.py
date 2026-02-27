# app/routes/recommendations.py
# Zilliz: POST /recommend is the primary book recommendation endpoint. Legacy GET routes retained for tracks and deprecated book cosine-similarity.
import os
import time

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from app.services.embedding_client import embed_text
from app.utils.db import get_mongo_collection
from app.services.recommendation_service import calculate_cosine_similarity_with_explanation

router = APIRouter()

# --- Zilliz book recommendations (POST /recommend) ---

COLLECTION_NAME = "books"
OUTPUT_FIELDS = [
    "work_key",
    "title",
    "author_name",
    "subjects",
    "description",
    "avg_rating",
    "has_rating",
    "rating_count",
    "want_to_read_count",
    "currently_reading_count",
    "already_read_count",
    "total_shelf_count",
    "cover_id",
]


class RecommendRequest(BaseModel):
    work_key: str
    title: str = ""
    author_name: str = ""
    subjects: list[str] = []


def _build_query_text(title: str, author_name: str, subjects: list) -> str:
    parts = []
    if title:
        parts.append(title)
    if author_name:
        parts.append(author_name)
    if subjects:
        parts.append(", ".join(subjects[:10]))
    return " | ".join(parts)


def _generate_new_id() -> int:
    """Generate INT64 id for Zilliz insert (Tier 2 write-back)."""
    return time.time_ns() // 1000


def _store_new_book(
    client,
    work_key: str,
    title: str,
    author_name: str,
    subjects: list,
    vector: list,
) -> None:
    """Write a fallback-generated record to Zilliz for future Tier 1 cache hits. Runs in background task."""
    try:
        client.insert(
            collection_name=COLLECTION_NAME,
            data=[
                {
                    "id": _generate_new_id(),
                    "work_key": work_key[:32],
                    "title": (title or "")[:512],
                    "author_name": (author_name or "")[:256],
                    "subjects": ", ".join((subjects or [])[:10])[:2048],
                    "description": "",
                    "avg_rating": 0.0,
                    "has_rating": False,
                    "rating_count": 0,
                    "want_to_read_count": 0,
                    "currently_reading_count": 0,
                    "already_read_count": 0,
                    "total_shelf_count": 0,
                    "cover_id": 0,
                    "embedding": vector,
                }
            ],
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Background Zilliz write failed for %s: %s", work_key, e)


def _validate_token(request: Request) -> None:
    secret = os.getenv("SECRET_TOKEN")
    if not secret:
        return
    auth = request.headers.get("Authorization")
    token = request.query_params.get("token")
    if auth and auth.startswith("Bearer "):
        token = token or auth[7:]
    if token != secret:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/recommend")
async def recommend_zilliz(request: RecommendRequest, background_tasks: BackgroundTasks, req: Request):
    """Book recommendations via Zilliz vector search. Tier 1: stored embedding; Tier 2: embedding API + async write; Tier 3: subject filter."""
    _validate_token(req)
    client = getattr(req.app.state, "zilliz_client", None)
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Recommendation service not configured (ZILLIZ_ENDPOINT / ZILLIZ_API_KEY)",
        )

    fallback_used = False
    embedding_unavailable = False
    # Escape work_key for filter (avoid injection)
    work_key_safe = request.work_key.replace("\\", "\\\\").replace('"', '\\"')

    # Tier 1: look up stored embedding by work_key
    existing = client.query(
        collection_name=COLLECTION_NAME,
        filter=f'work_key == "{work_key_safe}"',
        output_fields=["embedding"],
        limit=1,
    )

    if existing:
        query_vector = existing[0]["embedding"]
    else:
        # Tier 2: generate embedding via API from Open Library metadata; fall back to Tier 3 if API fails
        query_text = _build_query_text(request.title, request.author_name, request.subjects)
        if query_text:
            query_vector = await embed_text(query_text)
            if query_vector is not None:
                background_tasks.add_task(
                    _store_new_book,
                    client,
                    request.work_key,
                    request.title,
                    request.author_name,
                    request.subjects,
                    query_vector,
                )
                fallback_used = True
            else:
                query_vector = None
                embedding_unavailable = True
        else:
            query_vector = None

    if query_vector is not None:
        results = client.search(
            collection_name=COLLECTION_NAME,
            data=[query_vector],
            limit=11,
            output_fields=OUTPUT_FIELDS,
        )
        # results: list of lists (one per query vector); each hit may have 'entity' or flat output_fields
        hits = results[0] if results else []
        recommendations = []
        for h in hits:
            entity = h.get("entity") if isinstance(h.get("entity"), dict) else h
            if entity.get("work_key") != request.work_key:
                recommendations.append(entity)
            if len(recommendations) >= 10:
                break
    else:
        # Tier 3: subject filter — last resort
        fallback_used = True
        subject = (request.subjects or [None])[0]
        if subject:
            subject_safe = subject.replace("\\", "\\\\").replace('"', '\\"').replace("%", "\\%")
            recs = client.query(
                collection_name=COLLECTION_NAME,
                filter=f'subjects like "%{subject_safe}%"',
                output_fields=OUTPUT_FIELDS,
                limit=10,
            )
            recommendations = recs or []
        else:
            recommendations = []

    out = {"recommendations": recommendations, "fallback_used": fallback_used}
    if embedding_unavailable:
        out["embedding_unavailable"] = True
    # Hint when work_key-only request had no metadata: book not in Zilliz and no title/author/subjects to build embedding
    if not recommendations and not _build_query_text(request.title, request.author_name, request.subjects):
        out["hint"] = "Book not in catalog or no metadata provided. Send title, author_name, and subjects for similar books."
    return out


# --- Legacy route: track recommendations (MongoDB Tracks only). Book recommendations use POST /recommend (Zilliz). ---

@router.get("/recommendations/cosine-similarity/{track_id}")
async def recommend_songs(track_id: str, token: str, top_n: int = 10):
    secret_token = os.getenv("SECRET_TOKEN")
    if token != secret_token:
        raise HTTPException(status_code=401, detail="Invalid token")

    collection = get_mongo_collection()

    # Fetch the target song from MongoDB (Spotify fallback removed)
    target_song = collection.find_one({"track_id": track_id})

    required_features = ['danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness', 'image_url', 'popularity', 'acousticness', 'instrumentalness', 'liveness', 'tempo', 'time_signature', 'mode']

    # No longer fetch from Spotify; require target to exist in DB with full features
    if target_song is None:
        raise HTTPException(status_code=404, detail="Track not found in database. Spotify fallback removed for migration.")
    if not all(key in target_song for key in required_features):
        raise HTTPException(status_code=404, detail="Track missing required features in database. Spotify fallback removed for migration.")

    # Ensure necessary features exist and are non-null
    if not all(key in target_song and target_song[key] is not None for key in required_features):
        raise HTTPException(status_code=400, detail="Target song is missing necessary audio features")

    # Get all tracks with necessary features
    all_tracks = list(collection.find({key: {"$exists": True, "$ne": None} for key in required_features}, {
        "_id": 0, "track_id": 1, "track_name": 1, "artist_name": 1, "popularity": 1, **{key: 1 for key in required_features}
    }))

    # Define feature columns for similarity calculation
    feature_columns = ['popularity', 'danceability', 'energy', 'valence', 'loudness', 'key', 'speechiness']

    # Calculate recommendations with explanations
    recommended_tracks = calculate_cosine_similarity_with_explanation(target_song, all_tracks, feature_columns, top_n)

    return {
        "recommendations": recommended_tracks,
        "target_features": {key: target_song[key] for key in feature_columns},
    }


# #re-instate after adding ANNOY or FAISS for approximating nearest neighbors
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

#     # Define feature columns and weights
#     feature_columns = [
#         'acousticness', 'danceability', 'energy', 'instrumentalness',
#         'liveness', 'loudness', 'speechiness', 'tempo', 'valence', 'popularity'
#     ]

#     # Create a weights dictionary to pass into cosine similarity
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

#     # Calculate recommendations using weighted cosine similarity
#     recommended_tracks = calculate_weighted_cosine_similarity(target_song, all_tracks, feature_columns, top_n, weights)

#     return {"recommendations": recommended_tracks}