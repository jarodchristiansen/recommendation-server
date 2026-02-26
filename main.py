# app/main.py
import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymilvus import MilvusClient

from app.routes import recommendations

# Lazy-loaded so startup stays under low memory limits (e.g. Render 512MB).
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create Zilliz client at startup; load embedding model on first use (saves ~80MB at startup)."""
    endpoint = os.getenv("ZILLIZ_ENDPOINT")
    token = os.getenv("ZILLIZ_API_KEY")
    if endpoint and token:
        app.state.zilliz_client = MilvusClient(uri=endpoint, token=token)
        app.state.embedding_model = None  # Lazy-loaded in recommendations route
        app.state.embedding_model_name = EMBEDDING_MODEL_NAME
        app.state._embedding_model_lock = asyncio.Lock()
    else:
        app.state.zilliz_client = None
        app.state.embedding_model = None
        app.state.embedding_model_name = None
        app.state._embedding_model_lock = None
    yield
    # No explicit close required for MilvusClient; process exit is fine


app = FastAPI(lifespan=lifespan)

# Include recommendations routes
app.include_router(recommendations.router)


@app.get("/")
@app.head("/")
async def root():
    return {"message": "Hello World"}
