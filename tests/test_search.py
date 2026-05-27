"""Tests for the search endpoint of the ToolHunt Flask application."""

import json
from unittest.mock import patch


class TestSearchEndpoint:
    """Verify POST /search behaviors."""

    def test_search_returns_results(self, client):
        """Sending a valid query should return a 200 with results list."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "network scanner"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_search_result_has_expected_fields(self, client):
        """Each result should have name, description, link, and category."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "sql injection"}),
            content_type="application/json",
        )
        data = response.get_json()
        for tool in data["results"]:
            assert "name" in tool
            assert "description" in tool
            assert "link" in tool
            assert "category" in tool

    def test_empty_query_returns_400(self, client):
        """An empty query should return a 400 error."""
        response = client.post(
            "/search",
            data=json.dumps({"query": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_missing_query_returns_400(self, client):
        """A request without a 'query' field should return 400."""
        response = client.post(
            "/search",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    # ── Structured error response tests ───────────────────────────────────

    def test_error_response_has_code_and_retryable(self, client):
        """Error responses should include 'code' and 'retryable' fields."""
        # Trigger an error via invalid JSON
        response = client.post(
            "/search",
            data="not json",
            content_type="application/json",
        )
        # Flask returns 400 for bad JSON body — but our route logic won't be reached
        # Instead test via a mock that raises during search_tool
        from unittest.mock import patch
        from backend.main import search_tool as _original
        with patch("app.routes.search_tool", side_effect=RuntimeError("DB down")):
            response = client.post(
                "/search",
                data=json.dumps({"query": "network scanner"}),
                content_type="application/json",
            )
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data
        assert "code" in data
        assert data["code"] == "SEARCH_FAILED"
        assert "retryable" in data
        assert data["retryable"] is True

    def test_error_response_with_retryable_false(self, client):
        """400 errors should be non-retryable."""
        response = client.post(
            "/search",
            data=json.dumps({"query": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        # 400 errors should also have code/retryable for consistency
        assert "code" in data
        assert data["retryable"] is False

    # ── Pagination tests ─────────────────────────────────────────────

    def test_default_limit_is_applied(self, client):
        """Search should return at most 10 results by default."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "test query"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) <= 10
        assert "has_more" in data
        assert "total" in data

    def test_offset_returns_correct_slice(self, client):
        """Offset 10 should return results 11 onward."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "test query", "limit": 10, "offset": 10}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        # With 15 total results, offset 10 returns results 11-15 (5 items)
        assert len(data["results"]) == 5
        assert data["has_more"] is False
        assert data["total"] == 15

    def test_has_more_true_when_results_exceed_limit(self, client):
        """has_more should be true when more results exist beyond the current page."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "test query", "limit": 10, "offset": 0}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 10
        assert data["has_more"] is True
        assert data["total"] == 15

    def test_has_more_false_on_last_page(self, client):
        """has_more should be false on the last page."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "test query", "limit": 5, "offset": 10}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 5
        assert data["has_more"] is False
        assert data["total"] == 15

    def test_custom_limit_returns_correct_count(self, client):
        """Custom limit should return exactly that many results (up to total)."""
        response = client.post(
            "/search",
            data=json.dumps({"query": "test query", "limit": 3, "offset": 0}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 3
        assert data["has_more"] is True
        assert data["total"] == 15

    # ── Cache tests ────────────────────────────────────────────────────

    def test_repeated_identical_query_is_cached(self, client):
        """Repeated identical queries should hit the cache (search_tool called once)."""
        from backend.main import search_tool as _original_search
        with patch("app.routes.search_tool", wraps=_original_search) as mock_search:
            # First call — should call search_tool
            response1 = client.post(
                "/search",
                data=json.dumps({"query": "network scanner"}),
                content_type="application/json",
            )
            assert response1.status_code == 200
            first_call_count = mock_search.call_count

            # Second call with identical query — should use cache, not call search_tool
            response2 = client.post(
                "/search",
                data=json.dumps({"query": "network scanner"}),
                content_type="application/json",
            )
            assert response2.status_code == 200
            # search_tool should NOT have been called again
            assert (
                mock_search.call_count == first_call_count
            ), "Expected second identical query to hit cache (search_tool not called)"

    def test_different_query_bypasses_cache(self, client):
        """A different query should call search_tool again (cache miss)."""
        from backend.main import search_tool as _original_search
        with patch("app.routes.search_tool", wraps=_original_search) as mock_search:
            # First query
            client.post(
                "/search",
                data=json.dumps({"query": "network scanner"}),
                content_type="application/json",
            )
            first_call_count = mock_search.call_count
            assert first_call_count >= 1

            # Different query — should be a cache miss
            client.post(
                "/search",
                data=json.dumps({"query": "password cracker"}),
                content_type="application/json",
            )
            assert (
                mock_search.call_count > first_call_count
            ), "Expected different query to call search_tool again (cache miss)"

    # ── Security tests ─────────────────────────────────────────────────

    def test_security_headers_present(self, client):
        """Responses should include expected security headers."""
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert response.headers.get("Permissions-Policy") == "geolocation=(), microphone=(), camera=()"

    def test_rate_limiter_blocks_excess(self, client):
        """More than 30 requests should trigger a 429 error."""
        # Clean rate limiter state for tests
        from app.rate_limiter import rate_limiter
        rate_limiter._requests.clear()

        # Send 30 requests (should succeed/400 but not 429)
        for _ in range(30):
            response = client.post(
                "/search",
                data=json.dumps({"query": "test"}),
                content_type="application/json",
            )
            assert response.status_code != 429

        # 31st request should be blocked
        response = client.post(
            "/search",
            data=json.dumps({"query": "test"}),
            content_type="application/json",
        )
        assert response.status_code == 429
        data = response.get_json()
        assert data.get("code") == "RATE_LIMITED"


    def test_input_sanitization_strips_html(self, client):
        """HTML tags in the query should be stripped."""
        from unittest.mock import patch

        # We need to make sure the rate limiter isn't blocking us.
        from app.rate_limiter import rate_limiter
        rate_limiter._requests.clear()

        with patch("app.routes.search_tool") as mock_search:
            mock_search.return_value = []

            # Use cache.clear() to ensure cache miss if any
            from app.extensions import cache
            cache.clear()

            response = client.post(
                "/search",
                data=json.dumps({"query": "<script>alert('xss')</script>"}),
                content_type="application/json",
            )

            mock_search.assert_called_once_with("alert('xss')")
