# app/main.py
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pymilvus import MilvusClient

from app.routes import recommendations


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create Zilliz client at startup. Embeddings are done via external API (see embedding_client)."""
    endpoint = os.getenv("ZILLIZ_ENDPOINT")
    token = os.getenv("ZILLIZ_API_KEY")
    if endpoint and token:
        app.state.zilliz_client = MilvusClient(uri=endpoint, token=token)
    else:
        app.state.zilliz_client = None
    yield
    # No explicit close required for MilvusClient; process exit is fine


app = FastAPI(lifespan=lifespan)

# Include recommendations routes
app.include_router(recommendations.router)


@app.get("/")
@app.head("/")
async def root():
    return {"message": "Hello World"}
