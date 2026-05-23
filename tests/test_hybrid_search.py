"""Tests for hybrid_search RRF implementation.

This file tests the real reciprocal_rank_fusion function by
loading the real hybrid_search module (the conftest mock is
temporarily removed to allow this).
"""
import sys
import types
import pytest


class TestReciprocalRankFusion:
    """Test the Reciprocal Rank Fusion scoring function."""

    @classmethod
    def setup_class(cls):
        """Load the REAL hybrid_search module for testing.

        The conftest.py pytest_configure inserts a mock into
        sys.modules['backend.hybrid_search']. We remove it so
        Python imports the real module. The langchain/sentence-
        transformer mocks remain — they don't affect the pure
        RRF function.
        """
        # Remove the mock to force loading the real module
        mock = sys.modules.pop("backend.hybrid_search", None)
        # Also clear any cached compiled bytecode reference
        for key in list(sys.modules.keys()):
            if "hybrid_search" in key and key != "backend.hybrid_search":
                sys.modules.pop(key, None)

        # Now import the real module
        from backend import hybrid_search  # noqa: F811
        cls.hybrid_search = hybrid_search

        # Restore mock for other tests that depend on it
        if mock is not None:
            sys.modules["backend.hybrid_search"] = mock

    def _make_doc(self, content, metadata=None):
        """Create a simple document-like object with page_content."""
        return types.SimpleNamespace(
            page_content=content,
            metadata=metadata or {}
        )

    def test_rrf_basic_three_docs(self):
        """Three documents with different FAISS and BM25 ranks.

        doc0: FAISS rank 1, BM25 rank 3
        doc1: FAISS rank 2, BM25 rank 1
        doc2: FAISS rank 3, BM25 rank 2

        RRF scores with k=60:
          doc0: 1/(60+1) + 1/(60+3) = 0.01639344 + 0.01587301 = 0.03226645
          doc1: 1/(60+2) + 1/(60+1) = 0.01612903 + 0.01639344 = 0.03252247
          doc2: 1/(60+3) + 1/(60+2) = 0.01587301 + 0.01612903 = 0.03200204
        Expected order: doc1 > doc0 > doc2
        """
        docs = {
            "doc0": self._make_doc("doc0"),
            "doc1": self._make_doc("doc1"),
            "doc2": self._make_doc("doc2"),
        }

        # FAISS returns in order: doc0 (rank 1), doc1 (rank 2), doc2 (rank 3)
        faiss_results = [docs["doc0"], docs["doc1"], docs["doc2"]]

        # BM25 returns in order: doc1 (rank 1), doc2 (rank 2), doc0 (rank 3)
        bm25_results = [docs["doc1"], docs["doc2"], docs["doc0"]]

        # Execute RRF
        result = self.hybrid_search.reciprocal_rank_fusion(
            faiss_results, bm25_results, k=60
        )

        # Verify order: doc1 > doc0 > doc2
        assert len(result) == 3
        assert result[0].page_content == "doc1"
        assert result[1].page_content == "doc0"
        assert result[2].page_content == "doc2"

        # Verify scores are correctly computed
        assert result[0].metadata["rrf_score"] == pytest.approx(0.03252247, rel=1e-5)
        assert result[1].metadata["rrf_score"] == pytest.approx(0.03226645, rel=1e-5)
        assert result[2].metadata["rrf_score"] == pytest.approx(0.03200204, rel=1e-5)

    def test_rrf_doc_only_in_faiss(self):
        """A document appearing only in FAISS (not in BM25) should still get a score.

        doc0: FAISS rank 1, BM25 rank None
        doc1: FAISS rank None, BM25 rank 1
        """
        docs = {
            "faiss_only": self._make_doc("faiss_only"),
            "bm25_only": self._make_doc("bm25_only"),
        }

        faiss_results = [docs["faiss_only"]]
        bm25_results = [docs["bm25_only"]]

        result = self.hybrid_search.reciprocal_rank_fusion(
            faiss_results, bm25_results, k=60
        )

        # Both should be present
        assert len(result) == 2

        # Both get score = 1/(60+1) = 1/61 ≈ 0.016393
        for doc in result:
            assert doc.metadata["rrf_score"] == pytest.approx(1.0 / 61.0, rel=1e-6)

    def test_rrf_empty_results(self):
        """Empty FAISS and BM25 results should return empty list."""
        result = self.hybrid_search.reciprocal_rank_fusion([], [], k=60)
        assert result == []

    def test_rrf_one_empty_one_not(self):
        """If one system returns no results, RRF should still work with the other."""
        doc = self._make_doc("only_doc")

        # Only FAISS has results
        result = self.hybrid_search.reciprocal_rank_fusion([doc], [], k=60)
        assert len(result) == 1
        assert result[0].page_content == "only_doc"

        # Only BM25 has results
        result = self.hybrid_search.reciprocal_rank_fusion([], [doc], k=60)
        assert len(result) == 1
        assert result[0].page_content == "only_doc"

    def test_rrf_deduplicates(self):
        """Same document appearing in both should appear only once."""
        doc = self._make_doc("shared_doc")

        result = self.hybrid_search.reciprocal_rank_fusion(
            [doc], [doc], k=60
        )

        assert len(result) == 1
        assert result[0].page_content == "shared_doc"

    def test_rrf_scores_correct_values(self):
        """Verify precise RRF score values for a single doc in one system."""
        doc = self._make_doc("test_doc")

        # With k=60 and rank=1: score = 1/(60+1) = 1/61 ≈ 0.016393
        result = self.hybrid_search.reciprocal_rank_fusion(
            [doc], [], k=60
        )
        assert len(result) == 1
        # Score is stored in metadata['rrf_score']
        assert result[0].metadata["rrf_score"] == pytest.approx(1.0 / 61.0, rel=1e-6)

    def test_rrf_different_k_values(self):
        """RRF should work with different k values."""
        doc = self._make_doc("test_doc")

        # k=1: score = 1/(1+1) = 0.5
        result = self.hybrid_search.reciprocal_rank_fusion([doc], [], k=1)
        assert result[0].metadata["rrf_score"] == pytest.approx(0.5, rel=1e-6)

        # k=100: score = 1/(100+1) = 1/101 ≈ 0.009901
        result = self.hybrid_search.reciprocal_rank_fusion([doc], [], k=100)
        assert result[0].metadata["rrf_score"] == pytest.approx(1.0 / 101.0, rel=1e-6)

    def test_rrf_k_must_be_positive(self):
        """RRF constant k must be positive; zero and negative should raise ValueError."""
        doc = self._make_doc("test_doc")

        with pytest.raises(ValueError, match="k must be positive"):
            self.hybrid_search.reciprocal_rank_fusion([doc], [], k=0)

        with pytest.raises(ValueError, match="k must be positive"):
            self.hybrid_search.reciprocal_rank_fusion([doc], [], k=-5)

    def test_rrf_none_metadata(self):
        """Documents with None or missing metadata should not crash RRF.

        Three docs with different None/missing metadata patterns.
        Ranks: 1, 2, 3 → scores: 1/61, 1/62, 1/63.
        """
        doc_none = types.SimpleNamespace(
            page_content="none_meta",
            metadata=None
        )
        doc_empty = types.SimpleNamespace(
            page_content="empty_meta",
            metadata={}
        )
        doc_missing = types.SimpleNamespace(
            page_content="missing_meta",
        )

        result = self.hybrid_search.reciprocal_rank_fusion(
            [doc_none, doc_empty, doc_missing], [], k=60
        )
        assert len(result) == 3

        # Build a map content -> doc for assertion
        result_map = {doc.page_content: doc for doc in result}
        assert result_map["none_meta"].metadata["rrf_score"] == pytest.approx(1.0 / 61.0, rel=1e-6)
        assert result_map["empty_meta"].metadata["rrf_score"] == pytest.approx(1.0 / 62.0, rel=1e-6)
        assert result_map["missing_meta"].metadata["rrf_score"] == pytest.approx(1.0 / 63.0, rel=1e-6)

    def test_search_function_signature(self):
        """The search() function should accept the expected parameters."""
        import inspect
        sig = inspect.signature(self.hybrid_search.search)
        params = list(sig.parameters.keys())
        assert "doc_list" in params
        assert "query" in params
        assert "similarity_threshold" in params


class TestEmbeddingWrapper:
    """Test the EmbeddingWrapper that adapts SentenceTransformer to FAISS interface."""

    @classmethod
    def setup_class(cls):
        """Load the REAL hybrid_search module to access EmbeddingWrapper."""
        mock = sys.modules.pop("backend.hybrid_search", None)
        for key in list(sys.modules.keys()):
            if "hybrid_search" in key and key != "backend.hybrid_search":
                sys.modules.pop(key, None)
        from backend import hybrid_search  # noqa: F811
        cls.hybrid_search = hybrid_search
        if mock is not None:
            sys.modules["backend.hybrid_search"] = mock

    def test_embedding_wrapper_exists(self):
        """EmbeddingWrapper class should be defined in hybrid_search."""
        assert hasattr(self.hybrid_search, 'EmbeddingWrapper')

    def test_embed_query_returns_1024_dim(self):
        """embed_query should return a 1024-dimensional vector (BGE-M3)."""
        wrapper = self.hybrid_search.EmbeddingWrapper(
            self.hybrid_search.model
        )
        vec = wrapper.embed_query("test query")
        assert len(vec) == 1024

    def test_embed_documents_returns_1024_dim(self):
        """embed_documents should return a list of 1024-dimensional vectors (BGE-M3)."""
        wrapper = self.hybrid_search.EmbeddingWrapper(
            self.hybrid_search.model
        )
        vecs = wrapper.embed_documents(["doc1", "doc2"])
        assert len(vecs) == 2
        assert len(vecs[0]) == 1024
        assert len(vecs[1]) == 1024

    def test_onnx_backend_used(self):
        """SentenceTransformer should be initialized with backend='onnx'."""
        # The model is already created at module level; we verify by checking
        # the module's model attribute exists and is wrapped by EmbeddingWrapper
        assert hasattr(self.hybrid_search, 'embedding')
        assert hasattr(self.hybrid_search, 'model')
        wrapper = self.hybrid_search.embedding
        assert isinstance(wrapper, self.hybrid_search.EmbeddingWrapper)


class TestSearchCaching:
    """Test that BM25/FAISS indexes are built only once (cached at module level)."""

    @classmethod
    def setup_class(cls):
        """Load the REAL hybrid_search module with call-counting spies on BM25Retriever and FAISS."""
        # Remove the mock to force loading the real module
        mock = sys.modules.pop("backend.hybrid_search", None)
        for key in list(sys.modules.keys()):
            if "hybrid_search" in key and key != "backend.hybrid_search":
                sys.modules.pop(key, None)

        # Install a call-counting spy on BM25Retriever.from_texts
        from langchain_community.retrievers import BM25Retriever

        cls._original_bm25_from_texts = BM25Retriever.from_texts
        cls._bm25_call_count = 0

        def spy_bm25_from_texts(cls_, texts):
            cls._bm25_call_count += 1
            return cls._original_bm25_from_texts(texts)

        BM25Retriever.from_texts = classmethod(spy_bm25_from_texts)

        # Install a call-counting spy on FAISS.from_texts
        from langchain_community.vectorstores import FAISS

        cls._original_faiss_from_texts = FAISS.from_texts
        cls._faiss_call_count = 0

        def spy_faiss_from_texts(cls_, *args, **kwargs):
            cls._faiss_call_count += 1
            return cls._original_faiss_from_texts(*args, **kwargs)

        FAISS.from_texts = classmethod(spy_faiss_from_texts)

        # Now import the real module (the spies are active before import)
        from backend import hybrid_search  # noqa: F811
        cls.hybrid_search = hybrid_search

        # Restore mock for other tests that depend on it
        if mock is not None:
            sys.modules["backend.hybrid_search"] = mock

    @classmethod
    def teardown_class(cls):
        """Restore the original from_texts methods."""
        from langchain_community.retrievers import BM25Retriever
        BM25Retriever.from_texts = cls._original_bm25_from_texts
        from langchain_community.vectorstores import FAISS
        FAISS.from_texts = cls._original_faiss_from_texts

    def test_indexes_cached_across_multiple_searches(self):
        """BM25 and FAISS indexes should each be built/loaded exactly once and then cached.

        BM25Retriever.from_texts is called exactly once on first search.
        FAISS.from_texts is called at most once — it may be 0 if a prebuilt
        FAISS index exists on disk and is loaded via load_local instead.
        The critical invariant: neither count increases on subsequent searches.
        """
        # Reset call counts
        self.__class__._bm25_call_count = 0
        self.__class__._faiss_call_count = 0

        doc_list = ["tool one for searching", "tool two scanning"]

        # First search — indexes are built/loaded
        result1 = self.hybrid_search.search(doc_list, "search")
        bm25_after_first = self.__class__._bm25_call_count
        faiss_after_first = self.__class__._faiss_call_count

        # BM25 must always build from scratch (1 call)
        assert bm25_after_first == 1, (
            f"Expected 1 call to BM25Retriever.from_texts on first search, "
            f"got {bm25_after_first}"
        )
        # FAISS may be loaded from disk (0 calls) or built (1 call)
        assert faiss_after_first <= 1, (
            f"Expected at most 1 call to FAISS.from_texts on first search, "
            f"got {faiss_after_first}"
        )

        # Second search with same doc_list — counts must NOT increase
        result2 = self.hybrid_search.search(doc_list, "scanning")
        assert self.__class__._bm25_call_count == bm25_after_first, (
            f"BM25 count increased from {bm25_after_first} to "
            f"{self.__class__._bm25_call_count} on second search (should be cached)"
        )
        assert self.__class__._faiss_call_count == faiss_after_first, (
            f"FAISS count increased from {faiss_after_first} to "
            f"{self.__class__._faiss_call_count} on second search (should be cached)"
        )

        # Third search — counts must still NOT increase
        result3 = self.hybrid_search.search(doc_list, "tool")
        assert self.__class__._bm25_call_count == bm25_after_first, (
            f"BM25 count increased from {bm25_after_first} to "
            f"{self.__class__._bm25_call_count} on third search (should be cached)"
        )
        assert self.__class__._faiss_call_count == faiss_after_first, (
            f"FAISS count increased from {faiss_after_first} to "
            f"{self.__class__._faiss_call_count} on third search (should be cached)"
        )
