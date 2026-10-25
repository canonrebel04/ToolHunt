"""Lightweight helpers shared by the search backend and offline tooling.

Kept free of heavy ML imports so CI/scripts can compute index fingerprints
without loading the embedding model.
"""
import hashlib

MODEL_NAME = "BAAI/bge-m3"


def index_text(tool) -> str:
    """Text that gets embedded/indexed for a tool."""
    return f"{tool['name']} {tool['description']}".lower()


def doc_list_hash(doc_list) -> str:
    """Order-independent fingerprint of the indexed texts plus the embedding model."""
    h = hashlib.sha256(MODEL_NAME.encode())
    for text in sorted(set(doc_list)):
        h.update(b"\0" + text.encode("utf-8"))
    return h.hexdigest()
