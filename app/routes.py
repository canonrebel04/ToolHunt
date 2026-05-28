"""Application routes defined as a Flask Blueprint."""

import logging

from flask import Blueprint, render_template, request, jsonify
from backend.main import search_tool
from app.extensions import cache
from app.rate_limiter import rate_limiter
import re

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)



@main_bp.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    return response


@main_bp.before_request
def check_rate_limit():
    if request.endpoint == 'main.search_tools':
        ip = request.remote_addr or 'unknown'
        if not rate_limiter.is_allowed(ip):
            from flask import jsonify
            return jsonify({"error": "Rate limit exceeded", "code": "RATE_LIMITED", "retryable": True}), 429


def sanitize_query(query: str) -> str:
    """Strip HTML tags and limit length."""
    if not query or not query.strip():
        return ""
    clean = re.sub(r'<[^>]+>', '', query)
    clean = clean.strip()[:200]
    return clean

def _error_response(message, code="UNKNOWN", retryable=False, status=500):
    """Build a structured error response.

    Parameters
    ----------
    message : str
        Human-readable error description.
    code : str
        Machine-readable error code (e.g. SEARCH_FAILED, BAD_REQUEST).
    retryable : bool
        Whether the client may reasonably retry the same request.
    status : int
        HTTP status code.

    Returns
    -------
    Response
        Flask JSON response with ``error``, ``code`` and ``retryable`` keys.
    """
    return jsonify({
        "error": message,
        "code": code,
        "retryable": retryable,
    }), status


@main_bp.route('/')
def index():
    """Render the main search page."""
    return render_template('index.html')


@main_bp.route("/health", methods=["GET"])
def health():
    """Enhanced health check with component status."""
    status = {"status": "ok"}
    checks = {}

    # Database check
    try:
        from backend.main import _load_tools, _tools
        _load_tools()
        checks["database"] = {
            "status": "ok",
            "tools_count": len(_tools) if _tools else 0
        }
    except Exception as e:
        checks["database"] = {"status": "degraded", "error": str(e)}
        status["status"] = "degraded"

    # Model check
    try:
        from backend.hybrid_search import model
        checks["model"] = {
            "status": "ok",
            "type": type(model).__name__,
            "backend": "onnx"
        }
    except Exception as e:
        checks["model"] = {"status": "degraded", "error": str(e)}
        status["status"] = "degraded"

    # Cache check
    try:
        from app.extensions import cache
        cache.set("__health_check__", "ok", timeout=5)
        cache_hit = cache.get("__health_check__")
        checks["cache"] = {
            "status": "ok" if cache_hit == "ok" else "degraded",
            "type": type(cache).__name__
        }
    except Exception as e:
        checks["cache"] = {"status": "degraded", "error": str(e)}
        if status["status"] == "ok":
            status["status"] = "degraded"

    # Uptime
    import time
    checks["uptime"] = time.time()

    status["checks"] = checks
    status_code = 200 if status["status"] == "ok" else 503
    return jsonify(status), status_code


@main_bp.route('/search', methods=['POST'])
def search_tools():
    """Handle tool search requests.

    Expects JSON body with:
        query (str): The search query string.
        limit (int, optional): Max results per page (default: 10).
        offset (int, optional): Pagination offset (default: 0).

    Returns
    -------
    JSON response with sliced results, pagination metadata, or structured error.
    """
    data = request.get_json(silent=True)
    if data is None:
        return _error_response(
            "Invalid JSON body",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    query = sanitize_query(data.get('query', ''))

    try:
        limit = int(data.get('limit', 10))
        offset = int(data.get('offset', 0))
    except (ValueError, TypeError):
        return _error_response(
            "Invalid limit or offset format",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    # Enforce bounds
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    if not query:
        return _error_response(
            "No query provided",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    # Generate cache key from request parameters
    query_str = query if query else ''
    cache_key = f"search:{query_str}:{limit}:{offset}"
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        logger.info(
            "Cache HIT  | query=%r limit=%s offset=%s",
            query, limit, offset,
        )
        return cached_response

    logger.info(
        "Cache MISS | query=%r limit=%s offset=%s",
        query, limit, offset,
    )

    try:
        all_results = search_tool(query)
        total = len(all_results)

        # Convert results to a more JSON-friendly format
        formatted_results = []
        for tool in all_results:
            formatted_results.append({
                'name': tool[0],
                'description': tool[1],
                'link': tool[2] if len(tool) > 2 else '',
                'category': tool[3] if len(tool) > 3 else ''
            })

        # Apply pagination slice
        sliced = formatted_results[offset:offset + limit]
        has_more = (offset + limit) < total

        response = jsonify({
            'results': sliced,
            'has_more': has_more,
            'total': total
        })

        # Cache the response for subsequent identical requests
        cache.set(cache_key, response, timeout=300)

        return response

    except Exception as e:
        logger.exception("Search failed: query=%r limit=%s offset=%s", query, limit, offset)
        return _error_response(
            str(e),
            code="SEARCH_FAILED",
            retryable=True,
            status=500,
        )
