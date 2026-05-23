"""Application routes defined as a Flask Blueprint."""

from flask import Blueprint, render_template, request, jsonify
from backend.main import search_tool
from app.extensions import cache

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Render the main search page."""
    return render_template('index.html')


@main_bp.route('/search', methods=['POST'])
def search_tools():
    """Handle tool search requests.

    Expects JSON body with:
        query (str): The search query string.
        limit (int, optional): Max results per page (default: 10).
        offset (int, optional): Pagination offset (default: 0).

    Returns
    -------
    JSON response with sliced results, pagination metadata, or error.
    """
    data = request.get_json()
    query = data.get('query', '')
    limit = data.get('limit', 10)
    offset = data.get('offset', 0)

    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Generate cache key from request parameters
    cache_key = f"search:{query}:{limit}:{offset}"
    cached_response = cache.get(cache_key)
    if cached_response is not None:
        return cached_response

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
        return jsonify({'error': str(e)}), 500
