"""Cross-encoder reranker for fine-grained query-document relevance scoring.

Uses a lightweight cross-encoder model (cross-encoder/ms-marco-MiniLM-L-6-v2)
to rerank the top candidates from the initial hybrid (RRF) retrieval stage.
This gives finer-grained relevance than embedding cosine similarity alone.
"""
from sentence_transformers import CrossEncoder

# Lightweight cross-encoder model for reranking
MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_reranker = None


def get_reranker():
    """Get (or create) the singleton CrossEncoder instance.

    Returns:
        CrossEncoder: The loaded cross-encoder model instance.
    """
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(MODEL_NAME)
    return _reranker


def rerank(query, documents, top_k=10):
    """Rerank a list of documents by cross-encoder relevance to the query.

    Evaluates each (query, document_text) pair through the cross-encoder,
    which produces a relevance score.  Documents are then sorted by score
    descending and the top ``top_k`` are returned.

    Args:
        query:       The search query string.
        documents:   List of document-like objects with a ``page_content``
                     attribute (e.g. LangChain Document or SimpleNamespace).
        top_k:       Number of top-scoring documents to return (default 10).

    Returns:
        List of document objects sorted by cross-encoder score descending,
        limited to ``top_k`` items.  The original document objects (including
        any metadata) are preserved unmodified.
    """
    if not documents:
        return []

    pairs = [[query, doc.page_content] for doc in documents]
    scores = get_reranker().predict(pairs)

    scored = list(zip(scores, documents))
    scored.sort(key=lambda x: x[0], reverse=True)

    return [doc for _, doc in scored[:top_k]]
