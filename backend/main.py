"""Main module for tool search functionality.

Loads the tool database lazily: SQLite is not opened until the first call to
search_tool(). Results are returned as dicts keyed by stable tool ``id``.
"""

import functools
import threading

from . import db
from .hybrid_search import search
from .indexing import index_text

# Module-level cache for lazy-loaded tool data
_tools = None             # list[dict], active tools in DB order
_descriptions = None      # list[str], indexed text per tool (same order)
_descriptions_dict = None  # indexed text -> position in _tools
_category_docs = None     # category -> set of indexed texts
_lock = threading.Lock()

VALID_CATEGORIES = ("all",) + db.CATEGORIES


def _load_tools():
    """Load active tools from SQLite into the module-level cache (thread-safe, once)."""
    global _tools, _descriptions, _descriptions_dict, _category_docs

    if _tools is not None:
        return

    with _lock:
        if _tools is not None:
            return

        conn = db.connect()
        try:
            tools = db.load_tools(conn)
        finally:
            conn.close()

        descriptions = [index_text(t) for t in tools]

        descriptions_dict = {}
        category_docs = {c: set() for c in db.CATEGORIES}
        for idx, item in enumerate(descriptions):
            if item not in descriptions_dict:
                descriptions_dict[item] = idx
            category_docs.setdefault(tools[idx]["category"], set()).add(item)

        _descriptions = descriptions
        _descriptions_dict = descriptions_dict
        _category_docs = category_docs
        _tools = tools


def get_tool(tool_id):
    """Return the full tool record for ``tool_id`` (or alias), or None."""
    conn = db.connect()
    try:
        return db.get_tool(conn, tool_id)
    finally:
        conn.close()


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
    primary_dict = {}
    for idx, item in enumerate(primary_list):
        if item not in primary_dict:
            primary_dict[item] = idx

    return [primary_dict[q] for q in query_list if q in primary_dict]


@functools.lru_cache(maxsize=256)
def search_tool(query, category="all"):
    """Search tools, returning tool dicts in relevance order.

    Args:
        query (str): The search query string.
        category (str): 'all' (default), 'security' or 'general'.

    Returns:
        list[dict]: matching tool records (id, name, description, url, category, ...).
    """
    if category not in VALID_CATEGORIES:
        raise ValueError(f"category must be one of {VALID_CATEGORIES}")
    _load_tools()

    allowed = None if category == "all" else _category_docs.get(category, set())
    matching_descriptions = search(_descriptions, query.lower(), allowed=allowed)

    matching_indices = [_descriptions_dict[q] for q in matching_descriptions if q in _descriptions_dict]
    return [_tools[index] for index in matching_indices]
