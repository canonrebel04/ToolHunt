"""Smoke tests for the ToolHunt Flask application."""



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

    def test_health_endpoint_returns_degraded_on_database_error(self, client, monkeypatch):
        """Health check returns 503 if database check fails."""
        import sys
        backend_main = sys.modules.get("backend.main")
        def mock_load_tools():
            raise Exception("Database connection failed")
        monkeypatch.setattr(backend_main, "_load_tools", mock_load_tools)

        response = client.get("/health")
        assert response.status_code == 503
        data = response.get_json()
        assert data["status"] == "degraded"
        assert data["checks"]["database"]["status"] == "degraded"
        assert data["checks"]["database"]["error"] == "Database connection failed"
