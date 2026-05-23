from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from backend.reranker import rerank
import os
import threading


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


model = SentenceTransformer("BAAI/bge-m3", backend="onnx")
embedding = EmbeddingWrapper(model)
FAISS_INDEX_PATH = "./backend/faiss_index"  # Directory to save/load FAISS index
FAISS_INITIAL_K = 198  # Number of initial candidates from FAISS before RRF fusion

# Module-level cache for BM25 and FAISS indexes (built once, reused on every search)
_bm25_retriever = None
_faiss_vectorstore = None
_cached_doc_list = None
_index_lock = threading.Lock()


def build_or_load_faiss_index(doc_list, force_rebuild=False):
    if os.path.exists(FAISS_INDEX_PATH) and not force_rebuild:
        print("Loading FAISS index from disk...")
        vectorstore = FAISS.load_local(FAISS_INDEX_PATH, embedding, allow_dangerous_deserialization=True)
    else:
        print("Building FAISS index...")
        vectorstore = FAISS.from_texts(doc_list, embedding)
        vectorstore.save_local(FAISS_INDEX_PATH)
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


def search(doc_list, query, similarity_threshold=0.5):
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
    filtered_results = []
    for doc, distance in faiss_results_with_scores:
        similarity = 1.0 / (1.0 + distance)
        if similarity >= similarity_threshold:
            filtered_results.append(doc)

    # Get BM25 results (they don't have similarity scores in the same way)
    bm25_results = bm25_retriever.get_relevant_documents(query)

    # Apply Reciprocal Rank Fusion with k=60
    rrf_results = reciprocal_rank_fusion(filtered_results, bm25_results, k=60)

    # Cross-encoder reranker on top-20 RRF candidates for finer-grained relevance
    top_candidates = rrf_results[:20] if len(rrf_results) > 20 else rrf_results
    reranked = rerank(query, top_candidates, top_k=10)

    return [doc.page_content for doc in reranked]
