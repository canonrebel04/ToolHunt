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
    global _tools, _descriptions

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
        description_to_index = {}
        cursor.execute("SELECT * FROM tools")
        tools = cursor.fetchall()
        # ⚡ Bolt Optimization: Build O(1) hash map lookup for tool indices
        for idx, row in enumerate(tools):
            text = f"{row[0]} {row[1]}".lower()
            descriptions.append(text)
            if text not in description_to_index:
                description_to_index[text] = idx

        conn.commit()
        conn.close()

        global _description_to_index
        _descriptions = descriptions
        _description_to_index = description_to_index
        _tools = tools


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

    # Collect the full tool data for each matching index (preserving RRF order)
    # ⚡ Bolt Optimization: Use O(1) hash map lookup instead of O(n) list index
    matching_tools_data = []
    for desc in matching_descriptions:
        if desc in _description_to_index:
            matching_tools_data.append(_tools[_description_to_index[desc]])

    return matching_tools_data
