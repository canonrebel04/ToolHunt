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
        desc_to_idx = {}
        cursor.execute("SELECT * FROM tools")
        tools = cursor.fetchall()
        for idx, row in enumerate(tools):
            text = f"{row[0]} {row[1]}".lower()
            descriptions.append(text)
            if text not in desc_to_idx:
                desc_to_idx[text] = idx

        conn.commit()
        conn.close()

        # ⚡ Bolt: Pre-compute dictionary during load phase for O(1) index lookup
        _descriptions = descriptions
        _desc_to_idx = desc_to_idx
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

    # ⚡ Bolt: Use pre-computed dictionary for O(1) index lookup instead of rebuilding dict on every search
    # Collect the full tool data for each matching description (preserving RRF order)
    matching_tools_data = []
    for desc in matching_descriptions:
        if desc in _desc_to_idx:
            matching_tools_data.append(_tools[_desc_to_idx[desc]])

    return matching_tools_data
