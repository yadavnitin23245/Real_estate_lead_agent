"""Text embeddings behind a single ``embed()`` function.

Backend is chosen by ``EMBED_BACKEND``:

* ``local``   - sentence-transformers on CPU (default, free, multilingual)
* ``litellm`` - any provider LiteLLM supports, model from ``EMBED_MODEL``
* ``hash``    - deterministic fake vectors for tests / CI (no model download)

All vectors are L2-normalised and must have ``EMBED_DIM`` dimensions, which is
also the size of the ``listings.embedding`` column.
"""

from __future__ import annotations

import hashlib
import math
import re
import threading
from collections.abc import Sequence
from typing import Any

from app.config import get_settings

_model: Any = None
_lock = threading.Lock()


def _local_model() -> Any:
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                _model = SentenceTransformer(get_settings().embed_model, device="cpu")
    return _model


def _normalise(vec: Sequence[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [float(x) / norm for x in vec]


def _hash_embed(text: str, dim: int) -> list[float]:
    vec = [0.0] * dim
    for token in re.findall(r"\w+", text.lower()):
        h = hashlib.md5(token.encode()).digest()
        idx = int.from_bytes(h[:4], "little") % dim
        vec[idx] += 1.0 if h[4] % 2 == 0 else -1.0
    return _normalise(vec)


def embed_many(texts: Sequence[str], batch_size: int = 32) -> list[list[float]]:
    settings = get_settings()
    texts = [t or "" for t in texts]
    if not texts:
        return []

    if settings.embed_backend == "hash":
        vectors = [_hash_embed(t, settings.embed_dim) for t in texts]
    elif settings.embed_backend == "local":
        arr = _local_model().encode(
            list(texts), batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
        )
        vectors = [list(map(float, row)) for row in arr]
    else:  # litellm
        import litellm

        vectors = []
        for i in range(0, len(texts), batch_size):
            resp = litellm.embedding(model=settings.embed_model, input=list(texts[i : i + batch_size]))
            vectors.extend(_normalise(item["embedding"]) for item in resp.data)

    got = len(vectors[0])
    if got != settings.embed_dim:
        raise ValueError(
            f"Embedding model '{settings.embed_model}' returned {got} dims but EMBED_DIM="
            f"{settings.embed_dim}. Set EMBED_DIM to match and create a new migration."
        )
    return vectors


def embed(text: str) -> list[float]:
    return embed_many([text])[0]


def listing_embedding_text(title: str, locality: str, description: str) -> str:
    """The text we embed for a listing (title + locality give context to the description)."""
    return f"{title}. {locality}. {description}"
