# app/main.py
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from pymilvus import MilvusClient

load_dotenv()

from app.routes import recommendations

logger = logging.getLogger(__name__)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def _connect_zilliz(endpoint: str, token: str) -> MilvusClient:
    return MilvusClient(uri=endpoint, token=token)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create Zilliz client at startup. Embeddings are done via external API (see embedding_client)."""
    endpoint = os.getenv("ZILLIZ_ENDPOINT")
    token = os.getenv("ZILLIZ_API_KEY")
    if endpoint and token:
        timeout_s = float(os.getenv("ZILLIZ_CONNECT_TIMEOUT_SEC", "90"))
        loop = asyncio.get_running_loop()
        logger.info("Connecting to Zilliz (timeout %.0fs)...", timeout_s)
        try:
            app.state.zilliz_client = await asyncio.wait_for(
                loop.run_in_executor(None, _connect_zilliz, endpoint, token),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError as e:
            logger.error("Zilliz connect timed out after %.0fs", timeout_s)
            raise RuntimeError(
                f"Zilliz connection timed out after {timeout_s:.0f}s. "
                "Check ZILLIZ_ENDPOINT, ZILLIZ_API_KEY, network, and firewall."
            ) from e
        logger.info("Zilliz client ready")
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
