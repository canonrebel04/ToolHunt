"""Tests for backend.main lazy-loading behavior.

Verifies that the tool database is loaded on first search_tool() call,
not at module import time.
"""
import sys
import pytest


class TestLazyLoading:
    """Verify lazy-loading of tools database in backend.main."""

    @classmethod
    def setup_class(cls):
        """Load the REAL backend.main module for testing.

        The conftest.py pytest_configure inserts a mock into
        sys.modules['backend.main']. We remove it so Python imports
        the real module.
        """
        # Save the mock so we can restore it
        cls._mock_main = sys.modules.pop("backend.main", None)
        # Clear any cached submodule references
        for key in list(sys.modules.keys()):
            if key.startswith("backend.main") and key != "backend.main":
                sys.modules.pop(key, None)

        # Now import the real module
        import backend.main  # noqa: F811
        cls.real_main = backend.main

    @classmethod
    def teardown_class(cls):
        """Restore the mock for other tests."""
        if cls._mock_main is not None:
            sys.modules["backend.main"] = cls._mock_main

    def test_tools_is_none_before_first_search(self):
        """Before any search_tool() call, _tools should be None."""
        assert self.real_main._tools is None, (
            "Expected _tools to be None at import time (lazy load)"
        )

    def test_descriptions_is_none_before_first_search(self):
        """Before any search_tool() call, _descriptions should be None."""
        assert self.real_main._descriptions is None, (
            "Expected _descriptions to be None at import time (lazy load)"
        )

    def test_tools_loaded_after_search_call(self):
        """After first search_tool() call, _tools should be populated."""
        # Reset to ensure clean state
        self.real_main._tools = None
        self.real_main._descriptions = None

        # This should trigger lazy loading
        result = self.real_main.search_tool("test")

        # After search, tools should be loaded
        assert self.real_main._tools is not None
        assert len(self.real_main._tools) > 0

    def test_descriptions_loaded_after_search_call(self):
        """After first search_tool() call, _descriptions should be populated."""
        assert self.real_main._descriptions is not None
        assert len(self.real_main._descriptions) > 0

    def test_multiple_calls_do_not_reload(self):
        """Multiple search_tool() calls should use cached tools, not reload."""
        # Get the id of the first loaded tools list
        tools_id_first = id(self.real_main._tools)
        descs_id_first = id(self.real_main._descriptions)

        # Call search again
        self.real_main.search_tool("another query")

        # The objects should be the same (cached, not replaced)
        assert id(self.real_main._tools) == tools_id_first, (
            "Expected _tools to be the same object after second call (cached)"
        )
        assert id(self.real_main._descriptions) == descs_id_first, (
            "Expected _descriptions to be the same object after second call (cached)"
        )

    def test_third_call_still_cached(self):
        """Third call should also use cached tools."""
        tools_id_first = id(self.real_main._tools)
        descs_id_first = id(self.real_main._descriptions)

        self.real_main.search_tool("yet another query")

        assert id(self.real_main._tools) == tools_id_first
        assert id(self.real_main._descriptions) == descs_id_first

    def test_wal_mode_enabled(self):
        """Verify PRAGMA journal_mode is WAL after _load_tools()."""
        # Ensure it's loaded
        self.real_main.search_tool("test query")

        # Check actual database mode
        import sqlite3
        conn = sqlite3.connect("backend/database/tools.db")
        cursor = conn.cursor()
        mode = cursor.execute("PRAGMA journal_mode").fetchone()[0]
        conn.close()
        assert mode.lower() == "wal"
