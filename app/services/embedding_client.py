# app/services/embedding_client.py
# Hugging Face Inference API for book embeddings. Use same model (all-MiniLM-L6-v2)
# and normalize so vectors stay consistent with existing Zilliz data.
# Changing model or API breaks compatibility with vectors already in Zilliz.

import asyncio
import logging
import os
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

# Use router.huggingface.co; api-inference.huggingface.co returned 410 (no longer supported).
DEFAULT_EMBEDDING_URL = (
    "https://router.huggingface.co/pipeline/feature-extraction/"
    "sentence-transformers/all-MiniLM-L6-v2"
)
TIMEOUT_S = 15.0
RETRY_BACKOFF_S = 1.0


def _embedding_url() -> Optional[str]:
    url = os.getenv("EMBEDDING_API_URL", "").strip() or DEFAULT_EMBEDDING_URL
    token = os.getenv("EMBEDDING_API_TOKEN", "").strip()
    if not token:
        return None
    return url


async def embed_text(text: str) -> Optional[List[float]]:
    """
    Get a single normalized embedding for text from the configured API.
    Returns None on failure (no token, timeout, 4xx/5xx, invalid body);
    caller can fall back to Tier 3 (subject filter).
    """
    url = _embedding_url()
    if not url:
        logger.debug("Embedding API skipped: EMBEDDING_API_TOKEN not set")
        return None

    token = os.getenv("EMBEDDING_API_TOKEN", "").strip()
    payload = {"inputs": text, "normalize": True}
    headers = {"Authorization": f"Bearer {token}"}
    data = None

    for attempt in range(2):  # initial + one retry
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.warning(
                    "Embedding API returned %s: %s",
                    resp.status_code,
                    resp.text[:200] if resp.text else "",
                )
                return None
            data = resp.json()
            break
        except httpx.TimeoutException as e:
            logger.warning("Embedding API timeout (attempt %s): %s", attempt + 1, e)
            if attempt == 0:
                await asyncio.sleep(RETRY_BACKOFF_S)
            else:
                return None
        except (httpx.HTTPError, ValueError) as e:
            logger.warning("Embedding API error: %s", e)
            return None

    if data is None:
        return None

    # Response: list of vectors (one per input); we sent one string.
    if not isinstance(data, list) or len(data) < 1:
        logger.warning("Embedding API returned unexpected shape: %s", type(data))
        return None
    vec = data[0]
    if not isinstance(vec, list) or not all(isinstance(x, (int, float)) for x in vec):
        logger.warning("Embedding API vector invalid")
        return None
    return [float(x) for x in vec]
