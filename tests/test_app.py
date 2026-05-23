"""Smoke tests for the ToolHunt Flask application."""

import pytest


class TestAppRoutes:
    """Verify Flask app starts and basic routes respond."""

    def test_index_returns_200(self, client):
        """GET / should render the main search page."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"ToolHunt" in response.data
