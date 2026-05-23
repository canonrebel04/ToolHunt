"""Tests for the cross-encoder reranker module.

The conftest.py mocks sentence_transformers (including CrossEncoder),
so the real reranker module will use the mocked CrossEncoder during tests.
"""
import sys
import types
from unittest import mock
import pytest


class TestReranker:
    """Test the cross-encoder reranking functions."""

    @classmethod
    def setup_class(cls):
        """Load the REAL reranker module for testing.

        Removes any mock for backend.reranker from sys.modules so
        Python imports the real module.  The sentence_transformers mock
        (including CrossEncoder) remains in sys.modules from conftest.
        """
        # Remove any existing mock for backend.reranker
        _mock = sys.modules.pop("backend.reranker", None)
        for key in list(sys.modules.keys()):
            if "reranker" in key and key != "backend.reranker":
                sys.modules.pop(key, None)

        # Now import the real module
        from backend import reranker  # noqa: F811
        cls.reranker = reranker

        # Restore mock for other tests that depend on it
        if _mock is not None:
            sys.modules["backend.reranker"] = _mock

    def _make_doc(self, content, metadata=None):
        """Create a simple document-like object with page_content."""
        return types.SimpleNamespace(
            page_content=content,
            metadata=metadata or {}
        )

    # ── get_reranker() tests ──────────────────────────────────────────

    def test_get_reranker_returns_cross_encoder(self):
        """get_reranker() should return an object with a predict method."""
        reranker = self.reranker.get_reranker()
        assert hasattr(reranker, 'predict')
        assert callable(reranker.predict)

    def test_get_reranker_singleton(self):
        """get_reranker() should return the same instance on every call."""
        r1 = self.reranker.get_reranker()
        r2 = self.reranker.get_reranker()
        assert r1 is r2

    # ── rerank() tests ────────────────────────────────────────────────

    def test_rerank_empty_docs_returns_empty_list(self):
        """rerank() with an empty document list should return []."""
        result = self.reranker.rerank("query", [], top_k=10)
        assert result == []

    def test_rerank_returns_top_k_results(self):
        """rerank() should return exactly top_k results when enough docs exist."""
        docs = [self._make_doc(f"doc{i}") for i in range(5)]
        # Mock predict to return arbitrary scores
        with mock.patch.object(
            self.reranker.get_reranker(), 'predict',
            return_value=[0.1, 0.2, 0.3, 0.4, 0.5]
        ):
            result = self.reranker.rerank("query", docs, top_k=3)
        assert len(result) == 3

    def test_rerank_default_top_k_is_10(self):
        """rerank() should default to top_k=10 when not specified."""
        docs = [self._make_doc(f"doc{i}") for i in range(20)]
        with mock.patch.object(
            self.reranker.get_reranker(), 'predict',
            return_value=[float(i) for i in range(20)]
        ):
            result = self.reranker.rerank("query", docs)
        assert len(result) == 10

    def test_rerank_orders_by_score_descending(self):
        """rerank() should return documents ordered by score descending."""
        docs = [
            self._make_doc("low"),
            self._make_doc("high"),
            self._make_doc("medium"),
        ]
        # Scores in the order of docs passed: low=0.1, high=0.9, medium=0.5
        with mock.patch.object(
            self.reranker.get_reranker(), 'predict',
            return_value=[0.1, 0.9, 0.5]
        ):
            result = self.reranker.rerank("query", docs, top_k=3)

        assert len(result) == 3
        # Should be sorted: highest score first
        assert result[0].page_content == "high"
        assert result[1].page_content == "medium"
        assert result[2].page_content == "low"

    def test_rerank_fewer_docs_than_top_k(self):
        """rerank() should return all docs if top_k exceeds document count."""
        docs = [self._make_doc("only")]
        with mock.patch.object(
            self.reranker.get_reranker(), 'predict',
            return_value=[0.5]
        ):
            result = self.reranker.rerank("query", docs, top_k=10)
        assert len(result) == 1
        assert result[0].page_content == "only"

    def test_rerank_query_used_in_pairs(self):
        """rerank() should pass query-document pairs to predict."""
        docs = [self._make_doc("doc_a"), self._make_doc("doc_b")]
        expected_pairs = [["my_query", "doc_a"], ["my_query", "doc_b"]]

        with mock.patch.object(
            self.reranker.get_reranker(), 'predict',
            return_value=[0.8, 0.2]
        ) as mock_predict:
            self.reranker.rerank("my_query", docs, top_k=2)

        mock_predict.assert_called_once_with(expected_pairs)

    def test_rerank_preserves_document_metadata(self):
        """rerank() should preserve document metadata through reranking."""
        docs = [
            self._make_doc("doc_x", {"source": "faiss", "score": 0.95}),
            self._make_doc("doc_y", {"source": "bm25", "score": 0.85}),
        ]
        with mock.patch.object(
            self.reranker.get_reranker(), 'predict',
            return_value=[0.5, 0.9]
        ):
            result = self.reranker.rerank("query", docs, top_k=2)

        # doc_y has higher score (0.9), so it should come first
        assert result[0].page_content == "doc_y"
        assert result[0].metadata == {"source": "bm25", "score": 0.85}
        assert result[1].page_content == "doc_x"
        assert result[1].metadata == {"source": "faiss", "score": 0.95}
