"""Application routes defined as a Flask Blueprint."""

import logging

from flask import Blueprint, jsonify, render_template, request

from app.extensions import cache
from app.rate_limiter import rate_limiter
from backend.main import get_tool, search_tool

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: https:;"
    return response


@main_bp.before_request
def check_rate_limit():
    if request.endpoint == 'main.search_tools':
        ip = request.remote_addr or 'unknown'
        if not rate_limiter.is_allowed(ip):
            from flask import jsonify
            return jsonify({"error": "Rate limit exceeded", "code": "RATE_LIMITED", "retryable": True}), 429


def sanitize_query(query: str) -> str:
    """Normalize a search query: trim whitespace, drop control characters, cap length.

    The query is deliberately NOT HTML-escaped here. It is only ever used as
    search input and is never rendered into HTML by the server (responses are
    JSON). Escaping happens on output instead: the frontend writes the query
    back via ``input.value`` and escapes every result field with
    ``escapeHtml()`` before inserting it into the DOM. Escaping here would make
    searches containing ``&``, quotes or ``<``/``>`` look for HTML entities.
    """
    if not isinstance(query, str) or not query.strip():
        return ""
    clean = "".join(ch for ch in query if ch.isprintable() or ch == " ")
    return clean.strip()[:200]


CATEGORIES = ("all", "security", "general")


def format_tool(tool):
    """Public JSON shape of a search result."""
    return {
        'id': tool.get('id', ''),
        'name': tool.get('name', ''),
        'description': tool.get('description', ''),
        'link': tool.get('url', ''),
        'category': tool.get('category', ''),
        'subcategory': tool.get('subcategory', ''),
    }


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
    except Exception:
        logger.exception("Database health check failed")
        checks["database"] = {"status": "degraded", "error": "Database component is unavailable"}
        status["status"] = "degraded"

    # Model check
    try:
        from backend.hybrid_search import model
        checks["model"] = {
            "status": "ok",
            "type": type(model).__name__,
            "backend": "onnx"
        }
    except Exception:
        logger.exception("Model health check failed")
        checks["model"] = {"status": "degraded", "error": "Search model component is unavailable"}
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
    except Exception:
        logger.exception("Cache health check failed")
        checks["cache"] = {"status": "degraded", "error": "Cache component is unavailable"}
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
        category (str, optional): 'all' (default), 'security' or 'general'.

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

    category = str(data.get('category') or 'all').strip().lower()
    if category not in CATEGORIES:
        return _error_response(
            "Invalid category (use all, security or general)",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    try:
        limit = int(data.get('limit', 10))
        offset = int(data.get('offset', 0))
    except (ValueError, TypeError):
        return _error_response(
            "Invalid limit or offset parameter",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    limit = min(limit, 100)
    if limit < 1:
        limit = 10
    offset = max(offset, 0)

    if not query:
        return _error_response(
            "No query provided",
            code="BAD_REQUEST",
            retryable=False,
            status=400,
        )

    # Generate cache key from request parameters
    query_str = query if query else ''
    cache_key = f"search:{category}:{query_str}:{limit}:{offset}"
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
        all_results = search_tool(query, category)
        total = len(all_results)

        # Apply pagination slice before formatting to optimize
        sliced_results = all_results[offset:offset + limit]

        formatted_results = [format_tool(tool) for tool in sliced_results]

        has_more = (offset + limit) < total

        response = jsonify({
            'results': formatted_results,
            'has_more': has_more,
            'total': total
        })

        # Cache the response for subsequent identical requests
        cache.set(cache_key, response, timeout=300)

        return response

    except Exception:
        logger.exception("Search failed: query=%r limit=%s offset=%s", query, limit, offset)
        return _error_response(
            "An internal error occurred during search.",
            code="SEARCH_FAILED",
            retryable=True,
            status=500,
        )


@main_bp.route('/api/tools/<tool_id>', methods=['GET'])
def tool_detail(tool_id):
    """Return the full record for one tool."""
    tool_id = (tool_id or '').strip().lower()[:100]
    try:
        tool = get_tool(tool_id)
    except Exception:
        logger.exception("Tool lookup failed: id=%r", tool_id)
        return _error_response("An internal error occurred.", code="LOOKUP_FAILED", retryable=True, status=500)
    if tool is None:
        return _error_response("Tool not found", code="NOT_FOUND", retryable=False, status=404)
    out = format_tool(tool)
    for key in ('repo_url', 'tags', 'sources', 'language', 'license', 'stars', 'last_commit',
                'archived', 'first_seen', 'updated_at'):
        out[key] = tool.get(key)
    out['archived'] = bool(out['archived'])
    return jsonify(out)


@main_bp.route('/api/tools/<tool_id>/docs', methods=['GET'])
def tool_docs(tool_id):
    """Return the Tier 1 structured doc for a tool (flags, examples, install), if present."""
    tool_id = (tool_id or '').strip().lower()[:100]
    try:
        from docgen import schema
        tool = get_tool(tool_id)
        if tool is None:
            return _error_response("Tool not found", code="NOT_FOUND", retryable=False, status=404)
        doc = schema.load_doc(tool["id"]) or schema.load_doc(tool_id)
    except Exception:
        logger.exception("Docs lookup failed: id=%r", tool_id)
        return _error_response("An internal error occurred.", code="LOOKUP_FAILED", retryable=True, status=500)
    if doc is None:
        return _error_response("No documentation yet", code="NO_DOCS", retryable=False, status=404)
    return jsonify(doc)
