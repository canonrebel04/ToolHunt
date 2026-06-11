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
_desc_to_idx = None
_lock = threading.Lock()


def _load_tools():
    """Load tools from SQLite database into module-level cache.

    Uses double-checked locking for thread safety.
    Only executes once; subsequent calls are no-ops.
    """
    global _tools, _descriptions, _desc_to_idx

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

        _descriptions = descriptions

        # Build O(1) lookup dictionary for fast index resolution, keeping the first
        # occurrence of duplicates to match list.index() behavior.
        # We build it backwards so earlier items overwrite later ones.
        _desc_to_idx = {desc: idx for idx, desc in reversed(list(enumerate(descriptions)))}

        # Assign _tools LAST so the double-checked lock fast path
        # doesn't trigger before _desc_to_idx is populated.
        _tools = tools


def find_indices(primary_list, query_list, lookup_dict=None):
    """
    Find the indices of elements from query_list in primary_list.

    Args:
        primary_list (list): The list to search in
        query_list (list): The list of elements to search for
        lookup_dict (dict, optional): Precomputed dictionary mapping list elements
                                      to their indices for O(1) lookups.

    Returns:
        list: A list of indices where query elements are found in primary list
    """
    indices = []
    if lookup_dict is not None:
        for query_item in query_list:
            if query_item in lookup_dict:
                indices.append(lookup_dict[query_item])
    else:
        for query_item in query_list:
            try:
                index = primary_list.index(query_item)
                indices.append(index)
            except ValueError:
                pass
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
    matching_indices = find_indices(_descriptions, matching_descriptions, _desc_to_idx)

    # Collect the full tool data for each matching index (preserving RRF order)
    matching_tools_data = []
    for index in matching_indices:
        matching_tools_data.append(_tools[index])

    return matching_tools_data
