"""Verify the test infrastructure (mocks, fixtures) work correctly."""

import types


class TestMockInfrastructure:
    """Ensure our conftest mocks are properly installed."""

    def test_backend_main_is_mocked(self):
        """backend.main should be our fake module in sys.modules."""
        import sys
        assert "backend.main" in sys.modules
        bm = sys.modules["backend.main"]
        assert hasattr(bm, "search_tool")
        result = bm.search_tool("test")
        assert len(result) > 0
        assert result[0][0] == "nmap"

    def test_sentence_transformers_is_mocked(self):
        """sentence_transformers should be our fake module."""
        import sentence_transformers  # noqa: F811
        model = sentence_transformers.SentenceTransformer("fake")
        emb = model.encode_query("hello")
        assert isinstance(emb, list)
        assert len(emb) == 1024

    def test_flask_app_is_real(self):
        """The Flask app itself should be the real module, not a mock."""
        import flask
        assert hasattr(flask, "Flask")

    def test_conftest_module_types(self):
        """All mocked modules should be ModuleType instances."""
        import sys
        for name in [
            "backend.main",
            "backend.hybrid_search",
            "sentence_transformers",
        ]:
            assert name in sys.modules, f"{name} not in sys.modules"
            assert isinstance(sys.modules[name], types.ModuleType)
