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
_descriptions_to_index = None
_lock = threading.Lock()


def _load_tools():
    """Load tools from SQLite database into module-level cache.

    Uses double-checked locking for thread safety.
    Only executes once; subsequent calls are no-ops.
    """
    global _tools, _descriptions, _descriptions_to_index

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
        cursor.execute("SELECT * FROM tools")
        tools = cursor.fetchall()
        for row in tools:
            text = f"{row[0]} {row[1]}"
            descriptions.append(text.lower())

        conn.commit()
        conn.close()

        # Build an O(1) reverse index map.
        # Iterate backwards so that earlier items overwrite later ones,
        # ensuring we return the *first* occurrence just like list.index()
        descriptions_to_index = {}
        for idx, val in reversed(list(enumerate(descriptions))):
            descriptions_to_index[val] = idx

        _descriptions = descriptions
        _descriptions_to_index = descriptions_to_index
        _tools = tools


def find_indices(primary_list, query_list):
    """
    Find the indices of elements from query_list in primary_list.

    Args:
        primary_list (list): The list to search in
        query_list (list): The list of elements to search for

    Returns:
        list: A list of indices where query elements are found in primary list
    """
    # Build an O(1) reverse index map.
    # Iterate backwards so that earlier items overwrite later ones,
    # ensuring we return the *first* occurrence just like list.index()
    primary_to_index = {}
    for idx, val in reversed(list(enumerate(primary_list))):
        primary_to_index[val] = idx

    indices = []
    for query_item in query_list:
        if query_item in primary_to_index:
            indices.append(primary_to_index[query_item])
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

    # Find the indices of these matching descriptions using the O(1) module-level cache
    matching_indices = []
    for desc in matching_descriptions:
        if desc in _descriptions_to_index:
            matching_indices.append(_descriptions_to_index[desc])

    # Collect the full tool data for each matching index (preserving RRF order)
    matching_tools_data = []
    for index in matching_indices:
        matching_tools_data.append(_tools[index])

    return matching_tools_data
