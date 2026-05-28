"""Smoke tests for the ToolHunt Flask application."""

from unittest.mock import patch


class TestAppRoutes:
    """Verify Flask app starts and basic routes respond."""

    def test_index_returns_200(self, client):
        """GET / should render the main search page."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"ToolHunt" in response.data

    # ── Health endpoint tests ────────────────────────────────────────────

    def test_health_endpoint_returns_200(self, client):
        """GET /health should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert "database" in data["checks"]
        assert isinstance(data["checks"]["database"]["tools_count"], int)
        assert data["checks"]["database"]["tools_count"] >= 0

    def test_health_database_degraded(self, client):
        """Test health endpoint when database check fails."""
        with patch("backend.main._load_tools", side_effect=Exception("DB connection failed")):
            response = client.get("/health")
            assert response.status_code == 503
            data = response.get_json()
            assert data["status"] == "degraded"
            assert data["checks"]["database"]["status"] == "degraded"
            assert "error" in data["checks"]["database"]

    def test_health_cache_degraded(self, client):
        """Test health endpoint when cache check fails."""
        with patch("app.extensions.cache.set", side_effect=Exception("Cache error")):
            response = client.get("/health")
            assert response.status_code == 503
            data = response.get_json()
            assert data["status"] == "degraded"
            assert data["checks"]["cache"]["status"] == "degraded"
            assert "error" in data["checks"]["cache"]

    def test_health_model_degraded(self, client):
        """Test health endpoint when model check fails."""
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "backend.hybrid_search":
                raise Exception("Model loading failed")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            response = client.get("/health")
            assert response.status_code == 503
            data = response.get_json()
            assert data["status"] == "degraded"
            assert data["checks"]["model"]["status"] == "degraded"
            assert "error" in data["checks"]["model"]
