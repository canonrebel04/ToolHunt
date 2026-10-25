import contextlib
import json
import logging
import os
import threading
from pathlib import Path

from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from sentence_transformers import SentenceTransformer

from backend.indexing import MODEL_NAME, doc_list_hash
from backend.reranker import rerank

logger = logging.getLogger(__name__)


class EmbeddingWrapper:
    """Wraps a SentenceTransformer model to provide the FAISS-compatible interface.

    FAISS expects objects with `.embed_query(text)` and `.embed_documents(texts)`
    methods returning lists of floats.
    """

    def __init__(self, model):
        self.model = model

    def embed_query(self, text):
        return self.model.encode(text).tolist()

    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()


model = SentenceTransformer(MODEL_NAME, backend="onnx")
embedding = EmbeddingWrapper(model)
_REPO_ROOT = Path(__file__).resolve().parent.parent
# Directory to save/load the FAISS index (override with TOOLHUNT_INDEX_DIR, e.g. in tests)
FAISS_INDEX_PATH = os.environ.get("TOOLHUNT_INDEX_DIR", str(_REPO_ROOT / "backend" / "faiss_index"))
INDEX_META_FILE = "index_meta.json"
FAISS_INITIAL_K = 198  # Number of initial candidates from FAISS before RRF fusion
BM25_K = 100  # Number of BM25 candidates before RRF fusion (LangChain default is only 4)

# Module-level cache for BM25 and FAISS indexes (built once, reused on every search)
_bm25_retriever = None
_faiss_vectorstore = None
_cached_doc_list = None
_index_lock = threading.Lock()


def _read_index_hash(index_dir):
    try:
        with open(os.path.join(index_dir, INDEX_META_FILE), encoding="utf-8") as f:
            return json.load(f).get("doc_hash")
    except (OSError, ValueError):
        return None


@contextlib.contextmanager
def _build_lock(index_dir):
    """Cross-process lock so several gunicorn workers don't rebuild the index at once."""
    os.makedirs(index_dir, exist_ok=True)
    try:
        import fcntl
    except ImportError:  # pragma: no cover - non-POSIX
        yield
        return
    with open(os.path.join(index_dir, ".build.lock"), "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def _embedding_dim():
    try:
        return int(model.get_sentence_embedding_dimension())
    except (AttributeError, TypeError, ValueError):  # model stub without the method
        return None


def _load_if_compatible(index_dir):
    """Load the saved index, or return None if its vector size doesn't match the model."""
    store = FAISS.load_local(index_dir, embedding, allow_dangerous_deserialization=True)
    want_dim = _embedding_dim()
    have_dim = getattr(getattr(store, "index", None), "d", None)
    if isinstance(want_dim, int) and isinstance(have_dim, int) and want_dim != have_dim:
        logger.warning("FAISS index dim %s != model dim %s; rebuilding", have_dim, want_dim)
        return None
    return store


def build_or_load_faiss_index(doc_list, force_rebuild=False):
    """Load the on-disk FAISS index if it matches ``doc_list``, else (re)build and save it.

    A stale index (tools added/changed since it was built) is detected via the
    hash stored in ``index_meta.json`` and rebuilt automatically.
    """
    index_dir = FAISS_INDEX_PATH
    want = doc_list_hash(doc_list)
    index_file = os.path.join(index_dir, "index.faiss")
    if not force_rebuild and os.path.exists(index_file) and _read_index_hash(index_dir) == want:
        logger.info("Loading FAISS index from disk...")
        store = _load_if_compatible(index_dir)
        if store is not None:
            return store

    with _build_lock(index_dir):
        # Another worker may have finished the rebuild while we waited.
        if not force_rebuild and os.path.exists(index_file) and _read_index_hash(index_dir) == want:
            store = _load_if_compatible(index_dir)
            if store is not None:
                return store
        logger.info("Building FAISS index for %d documents (stale or missing)...", len(doc_list))
        vectorstore = FAISS.from_texts(doc_list, embedding)
        vectorstore.save_local(index_dir)
        with open(os.path.join(index_dir, INDEX_META_FILE), "w", encoding="utf-8") as f:
            json.dump({"doc_hash": want, "model": MODEL_NAME, "dim": _embedding_dim(),
                       "count": len(doc_list)}, f, indent=2)
    return vectorstore


def _ensure_indexes(doc_list):
    """Build BM25 and FAISS indexes on first call, then reuse cached instances.

    Uses double-checked locking for thread safety. Rebuilds indexes if
    doc_list changes between calls (guarded by _cached_doc_list).

    Args:
        doc_list: List of tool description strings to index.

    Returns:
        Tuple of (bm25_retriever, faiss_vectorstore).
    """
    global _bm25_retriever, _faiss_vectorstore, _cached_doc_list
    if _bm25_retriever is None or _cached_doc_list != doc_list:
        with _index_lock:
            if _bm25_retriever is None or _cached_doc_list != doc_list:
                _cached_doc_list = doc_list
                _bm25_retriever = BM25Retriever.from_texts(doc_list)
                _bm25_retriever.k = BM25_K
                _faiss_vectorstore = build_or_load_faiss_index(doc_list)
    return _bm25_retriever, _faiss_vectorstore


def reciprocal_rank_fusion(faiss_results, bm25_results, k=60):
    """Combine FAISS and BM25 results using Reciprocal Rank Fusion.

    RRF formula: score(d) = 1/(k + rank_faiss(d)) + 1/(k + rank_bm25(d))

    Where rank is the 1-based position of the document in each system's
    result list. If a document does not appear in a system's results, that
    term contributes 0.

    Args:
        faiss_results: List of Documents in FAISS rank order (1st = rank 1).
        bm25_results:  List of Documents in BM25 rank order  (1st = rank 1).
        k:             RRF constant (default 60, standard in Elasticsearch/
                       Qdrant/OpenSearch). Must be positive.

    Returns:
        List of Documents sorted by RRF score descending, with no duplicates.
        Each document's metadata is updated with its 'rrf_score'.

    Raises:
        ValueError: If k is not positive.
    """
    if k <= 0:
        raise ValueError("RRF constant k must be positive")

    if not faiss_results and not bm25_results:
        return []

    # Build rank maps: {page_content: rank} (1-based)
    faiss_ranks = {
        doc.page_content: idx + 1
        for idx, doc in enumerate(faiss_results)
    }
    bm25_ranks = {
        doc.page_content: idx + 1
        for idx, doc in enumerate(bm25_results)
    }

    # Collect all unique documents keyed by page_content,
    # keeping the first occurrence (FAISS preference for tie-breaking)
    all_docs = {}
    for doc in faiss_results:
        all_docs[doc.page_content] = doc
    for doc in bm25_results:
        if doc.page_content not in all_docs:
            all_docs[doc.page_content] = doc

    # Compute RRF scores and sort
    scored_docs = []
    for doc in all_docs.values():
        faiss_rank = faiss_ranks.get(doc.page_content)
        bm25_rank = bm25_ranks.get(doc.page_content)

        score = 0.0
        if faiss_rank is not None:
            score += 1.0 / (k + faiss_rank)
        if bm25_rank is not None:
            score += 1.0 / (k + bm25_rank)

        doc.metadata = dict(doc.metadata) if hasattr(doc, 'metadata') and doc.metadata else {}
        doc.metadata['rrf_score'] = score
        scored_docs.append((score, doc))

    # Sort by RRF score descending, tie-break by content for stability
    scored_docs.sort(key=lambda x: (-x[0], x[1].page_content))
    return [doc for _, doc in scored_docs]


def search(doc_list, query, similarity_threshold=0.5, allowed=None, top_k=10):
    """Hybrid search over ``doc_list``.

    ``allowed``: optional set of doc texts to restrict results to (used for the
    security/general category filter). Filtering happens before RRF/reranking
    so the reranker only sees eligible documents.
    """
    # Use cached BM25 and FAISS indexes (built once at module level)
    bm25_retriever, faiss_vectorstore = _ensure_indexes(doc_list)

    # Get FAISS results with real scores using similarity_search_with_score
    # Returns list of (Document, float_score) tuples where score is L2 distance
    faiss_results_with_scores = faiss_vectorstore.similarity_search_with_score(
        query, k=FAISS_INITIAL_K
    )

    # Filter FAISS results by similarity threshold
    # Convert L2 distance to similarity: similarity = 1 / (1 + distance)
    # This maps distance [0, ∞) to similarity (0, 1]
    # ⚡ Bolt: Use list comprehension for faster tight-loop execution
    filtered_results = [
        doc for doc, distance in faiss_results_with_scores
        if 1.0 / (1.0 + distance) >= similarity_threshold
    ]

    # Get BM25 results (they don't have similarity scores in the same way)
    bm25_results = bm25_retriever.get_relevant_documents(query)

    if allowed is not None:
        filtered_results = [d for d in filtered_results if d.page_content in allowed]
        bm25_results = [d for d in bm25_results if d.page_content in allowed]

    # Apply Reciprocal Rank Fusion with k=60
    rrf_results = reciprocal_rank_fusion(filtered_results, bm25_results, k=60)

    # Cross-encoder reranker on top-20 RRF candidates for finer-grained relevance
    top_candidates = rrf_results[:20] if len(rrf_results) > 20 else rrf_results
    reranked = rerank(query, top_candidates, top_k=top_k)

    return [doc.page_content for doc in reranked]
