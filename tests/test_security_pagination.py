import json

def test_invalid_limit_offset_returns_400(client):
    """Passing invalid limit or offset should return a 400 error."""
    # We need to ensure cache miss or hit doesn't matter, but routes will handle it.
    response = client.post(
        "/search",
        data=json.dumps({"query": "test query", "limit": "a", "offset": "b"}),
        content_type="application/json",
    )
    assert response.status_code == 400
    data = response.get_json()
    assert data["code"] == "BAD_REQUEST"
    assert "Invalid pagination parameters" in data["error"]

def test_limit_bounds_enforced(client):
    """Test that limit is clamped between 1 and 50."""
    from unittest.mock import patch
    with patch("app.routes.search_tool", return_value=[("n1", "d1", "l1", "c1")]*100):
        # Request limit 100
        response = client.post(
            "/search",
            data=json.dumps({"query": "test bounds", "limit": 100}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 50  # Should be clamped to 50

        # Request limit -5
        response = client.post(
            "/search",
            data=json.dumps({"query": "test bounds 2", "limit": -5}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["results"]) == 1  # Should be clamped to 1
