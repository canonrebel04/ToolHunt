"""Lightweight helpers shared by the search backend and offline tooling.

Kept free of heavy ML imports so CI/scripts can compute index fingerprints
without loading the embedding model.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

MODEL_NAME = "BAAI/bge-m3"
# Bump when the indexed text shape changes so FAISS/BM25 rebuild.
INDEX_TEXT_VERSION = "v2-enriched-docs"
# ~512 BGE-M3 tokens ≈ 2k chars of English; keep a little headroom.
MAX_INDEX_CHARS = 2000

logger = logging.getLogger(__name__)

_docs_cache: dict[str, dict] | None = None


def docs_dir() -> Path:
    return Path(os.environ.get(
        "TOOLHUNT_DOCS_DIR",
        Path(__file__).resolve().parent.parent / "data" / "docs",
    ))


def load_docs_map(root: Path | None = None, *, force: bool = False) -> dict[str, dict]:
    """Load ``data/docs/<id>.json`` into an id→doc map (cached)."""
    global _docs_cache
    if _docs_cache is not None and not force and root is None:
        return _docs_cache
    base = root or docs_dir()
    out: dict[str, dict] = {}
    if not base.is_dir():
        if root is None:
            _docs_cache = out
        return out
    for path in base.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                doc = json.load(f)
        except (OSError, ValueError) as e:
            logger.warning("skip bad doc %s: %s", path.name, e)
            continue
        tid = (doc.get("id") or path.stem or "").strip().lower()
        if tid:
            out[tid] = doc
    if root is None:
        _docs_cache = out
    return out


def _as_list(value) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except ValueError:
            pass
        return [value] if value.strip() else []
    return []


def _truncate(text: str, limit: int = MAX_INDEX_CHARS) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0]
    return cut or text[:limit]


def index_text(tool, doc: dict | None = None) -> str:
    """Text that gets embedded/indexed for a tool (enriched with Tier-1 docs when present)."""
    parts: list[str] = [
        str(tool.get("name") or ""),
        str(tool.get("description") or ""),
        str(tool.get("category") or ""),
        str(tool.get("subcategory") or ""),
    ]
    for tag in _as_list(tool.get("tags")):
        parts.append(str(tag))

    if doc is None:
        docs = load_docs_map()
        doc = docs.get(str(tool.get("id") or "").lower()) or docs.get(str(tool.get("name") or "").lower())

    if doc:
        parts.append(str(doc.get("summary") or ""))
        for h in doc.get("highlights") or []:
            parts.append(str(h))
        for sc in doc.get("subcommands") or []:
            if isinstance(sc, dict):
                parts.append(str(sc.get("name") or ""))
                parts.append(str(sc.get("description") or ""))
            else:
                parts.append(str(sc))
        # Flag names (helps BM25 on --thorough / -sV) + top descriptions
        for i, f in enumerate(doc.get("flags") or []):
            if not isinstance(f, dict):
                continue
            parts.append(str(f.get("name") or ""))
            parts.append(str(f.get("short") or ""))
            if i < 40:
                parts.append(str(f.get("description") or ""))
        for ex in (doc.get("examples") or [])[:6]:
            if isinstance(ex, dict):
                parts.append(str(ex.get("cmd") or ""))
                parts.append(str(ex.get("explanation") or ""))

    return _truncate(" ".join(p for p in parts if p).lower())


def doc_list_hash(doc_list) -> str:
    """Order-independent fingerprint of the indexed texts plus the embedding model."""
    h = hashlib.sha256(f"{MODEL_NAME}|{INDEX_TEXT_VERSION}".encode())
    for text in sorted(set(doc_list)):
        h.update(b"\0" + text.encode("utf-8"))
    return h.hexdigest()
