"""语义检索的嵌入模型加载（API 与 Web 共用）。"""
from __future__ import annotations

import os

import steeldig_db.config  # noqa: F401  加载 .env

EMBED_MODEL = os.environ.get("STEELDIG_EMBED_MODEL") or None
MODEL_CACHE = str(steeldig_db.config.settings.model_cache)

_embedder = None


def get_embedder():
    """懒加载；失败返回 None，调用方据此降级。"""
    global _embedder
    if _embedder is not None:
        return _embedder or None
    if not EMBED_MODEL:
        _embedder = False
        return None
    try:
        from fastembed import TextEmbedding

        _embedder = TextEmbedding(model_name=EMBED_MODEL, cache_dir=MODEL_CACHE)
    except Exception:  # noqa: BLE001
        _embedder = False
    return _embedder or None


def embed_query(text: str) -> str | None:
    """返回 pgvector 文本字面量；模型不可用时返回 None。"""
    emb = get_embedder()
    if emb is None:
        return None
    prefix = "query: " if "e5" in (EMBED_MODEL or "").lower() else ""
    v = next(iter(emb.query_embed([f"{prefix}{text}"])))
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"
