"""Application routes defined as a Flask Blueprint."""

import logging

from flask import Blueprint, render_template, request, jsonify
from backend.main import search_tool
from app.extensions import cache
from app.audit_logger import log_search_event, log_error_event, log_rate_limit_event
import time

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


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


@main_bp.after_request
def add_security_headers(response):
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' https://cdnjs.cloudflare.com; "
        "style-src 'self' https://cdnjs.cloudflare.com 'unsafe-inline'; "
        "font-src 'self' https://cdnjs.cloudflare.com data:; "
        "img-src 'self' data: https://raw.githubusercontent.com; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "form-action 'self'"
    )
    return response


@main_bp.route('/')
def index():
    """Render the main search page."""
    return render_template('index.html')


@main_bp.route('/health')
def health():
    """Health-check endpoint.

    Returns the server status and the count of tools available in the
    search backend so the frontend can decide whether to attempt searches.
    """
    try:
        # Use a broad query to get a sense of database health
        all_results = search_tool("*")
        tools_count = len(all_results)
    except Exception:
        logger.exception("Health check: search_tool failed")
        return jsonify({
            "status": "degraded",
            "tools_count": 0,
        }), 200

    return jsonify({
        "status": "ok",
        "tools_count": tools_count,
    })


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

    query = data.get('query', '')
    limit = data.get('limit', 10)
    offset = data.get('offset', 0)

    if not query:
        return _error_response(
            "No query provided",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    # Generate cache key from request parameters
    cache_key = f"search:{query}:{limit}:{offset}"
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
        start_time = time.time()
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

        duration_ms = (time.time() - start_time) * 1000
        ip = request.remote_addr or 'unknown'
        log_search_event(ip, query, total, duration_ms)

        return response

    except Exception as e:
        logger.exception("Search failed: query=%r limit=%s offset=%s", query, limit, offset)
        ip = request.remote_addr or 'unknown'
        log_error_event(ip, '/search', str(e))
        return _error_response(
            str(e),
            code="SEARCH_FAILED",
            retryable=True,
            status=500,
        )
