"""Tests for main Flask application routes."""

import pytest


class TestAppRoutes:
    """Verify standard application endpoints."""

    def test_index_returns_200(self, client):
        """GET / should render the main search page."""
        response = client.get("/")
        assert response.status_code == 200

    def test_health_endpoint_returns_200(self, client):
        """GET /health should return 200 with status ok."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "ok"
        assert "tools_count" in data
        assert isinstance(data["tools_count"], int)
        assert data["tools_count"] > 0

    def test_compression_headers(self, client):
        """Verify response compression is active."""
        # Use a large limit to generate a response > 500 bytes
        response = client.post(
            '/search',
            json={'query': 'nmap', 'limit': 100},
            headers={'Accept-Encoding': 'gzip'}
        )
        assert response.status_code == 200
        assert response.headers.get('Content-Encoding') == 'gzip'
