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
_description_to_index = None
_lock = threading.Lock()


def _load_tools():
    """Load tools from SQLite database into module-level cache.

    Uses double-checked locking for thread safety.
    Only executes once; subsequent calls are no-ops.
    """
    global _tools, _descriptions, _description_to_index

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

        description_to_index = {}
        for idx, desc in enumerate(descriptions):
            if desc not in description_to_index:
                description_to_index[desc] = idx

        _description_to_index = description_to_index
        _tools = tools
        _descriptions = descriptions


def find_indices(primary_list, query_list):
    """
    Find the indices of elements from query_list in primary_list.

    Args:
        primary_list (list): The list to search in
        query_list (list): The list of elements to search for

    Returns:
        list: A list of indices where query elements are found in primary list
    """
    # ⚡ Bolt: Cache index lookup for O(1) retrieval instead of O(N) list.index(). Reduces time complexity from O(N*M) to O(N+M)
    if primary_list is _descriptions and _description_to_index is not None:
        primary_dict = _description_to_index
    else:
        primary_dict = {}
        for idx, item in enumerate(primary_list):
            if item not in primary_dict:
                primary_dict[item] = idx

    return [primary_dict[q] for q in query_list if q in primary_dict]


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
