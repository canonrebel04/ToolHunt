"""Main module for tool search functionality.

Loads tool database lazily — the SQLite DB is not opened until
the first call to search_tool(). This avoids paying the import-time
cost of loading all 2,860 tools when the module is imported but not
yet used (e.g., during test collection with mocked backends).
"""

import sqlite3
import threading

from .hybrid_search import search

# Module-level cache for lazy-loaded tool data
_tools = None
_descriptions = None
_descriptions_map = None
_lock = threading.Lock()


def _load_tools():
    """Load tools from SQLite database into module-level cache.

    Uses double-checked locking for thread safety.
    Only executes once; subsequent calls are no-ops.
    """
    global _tools, _descriptions, _descriptions_map

    # Fast path: already loaded
    if _tools is not None:
        return

    with _lock:
        # Double-check: another thread may have loaded while we waited
        if _tools is not None:
            return

        conn = sqlite3.connect("backend/database/tools.db")
        cursor = conn.cursor()

        descriptions = []
        descriptions_map = {}
        cursor.execute("SELECT * FROM tools")
        tools = cursor.fetchall()
        for idx, row in enumerate(tools):
            text = f"{row[0]} {row[1]}".lower()
            descriptions.append(text)
            if text not in descriptions_map:
                descriptions_map[text] = idx

        conn.commit()
        conn.close()

        _tools = tools
        _descriptions = descriptions
        _descriptions_map = descriptions_map


def find_indices(primary_list, query_list):
    """
    Find the indices of elements from query_list in primary_list.

    Args:
        primary_list (list): The list to search in
        query_list (list): The list of elements to search for

    Returns:
        list: A list of indices where query elements are found in primary list
    """
    indices = []
    # Use cached O(1) map if searching in _descriptions, else fallback to building map
    if primary_list is _descriptions and _descriptions_map is not None:
        for query_item in query_list:
            if query_item in _descriptions_map:
                indices.append(_descriptions_map[query_item])
    else:
        # Fallback O(N) map build for other lists
        primary_map = {}
        for idx, item in enumerate(primary_list):
            if item not in primary_map:
                primary_map[item] = idx
        for query_item in query_list:
            if query_item in primary_map:
                indices.append(primary_map[query_item])
    return indices


def search_tool(query):
    """
    Searches for tools based on a query and returns the matching tool data
    in RRF-optimal order.

    The tool database is lazy-loaded on the first call to this function.

    Args:
        query (str): The search query string.

    Returns:
        list: A list of tuples, where each tuple represents a matching tool's data
              (name, description, url).
    """
    # Ensure tools are loaded from DB (lazy load)
    _load_tools()

    # Find matching tool descriptions based on the query (returned in RRF order)
    matching_descriptions = search(_descriptions, query.lower())

    # Find the indices of these matching descriptions in the main descriptions list
    matching_indices = find_indices(_descriptions, matching_descriptions)

    # Collect the full tool data for each matching index (preserving RRF order)
    matching_tools_data = []
    for index in matching_indices:
        matching_tools_data.append(_tools[index])

    return matching_tools_data
