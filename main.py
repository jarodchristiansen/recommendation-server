# app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

from app.routes import recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load MiniLM and Zilliz client once at startup (free-tier: ~80MB, few seconds cold start)."""
    endpoint = os.getenv("ZILLIZ_ENDPOINT")
    token = os.getenv("ZILLIZ_API_KEY")
    if endpoint and token:
        app.state.zilliz_client = MilvusClient(uri=endpoint, token=token)
        app.state.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    else:
        app.state.zilliz_client = None
        app.state.embedding_model = None
    yield
    # No explicit close required for MilvusClient; process exit is fine


app = FastAPI(lifespan=lifespan)

# Include recommendations routes
app.include_router(recommendations.router)


@app.get("/")
@app.head("/")
async def root():
    return {"message": "Hello World"}
