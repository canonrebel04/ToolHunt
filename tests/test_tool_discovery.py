from unittest.mock import patch, MagicMock
from backend.tool_discovery import (
    discover_new_tools,
    check_existing,
    fetch_awesome_security_list,
)
import urllib.error

# Mock data
MOCK_TOOLS = [
    {"name": "Tool1", "description": "Desc1", "url": "http://tool1"},
    {"name": "Tool2", "description": "Desc2", "url": "http://tool2"},
]


@patch("backend.tool_discovery.fetch_awesome_security_list")
@patch("backend.tool_discovery.check_existing")
def test_discover_returns_dict(mock_check_existing, mock_fetch):
    mock_fetch.return_value = MOCK_TOOLS
    mock_check_existing.return_value = False

    result = discover_new_tools(dry_run=True)

    assert isinstance(result, dict)
    assert "scanned" in result
    assert "added" in result
    assert "skipped_duplicates" in result
    assert "errors" in result
    assert "sources" in result

    assert result["scanned"] == 2
    assert result["added"] == 2
    assert result["skipped_duplicates"] == 0


@patch("backend.tool_discovery.DatabaseUpdater")
@patch("backend.tool_discovery.fetch_awesome_security_list")
@patch("backend.tool_discovery.check_existing")
def test_dry_run_does_not_insert(mock_check, mock_fetch, mock_updater_class):
    mock_fetch.return_value = MOCK_TOOLS
    mock_check.return_value = False
    mock_updater_instance = MagicMock()
    mock_updater_class.return_value = mock_updater_instance

    discover_new_tools(dry_run=True)

    mock_updater_instance.update_db.assert_not_called()


@patch("sqlite3.connect")
def test_check_existing_finds_duplicate(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (1,)
    mock_conn.__enter__.return_value.execute.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    assert check_existing("DuplicateTool") is True


@patch("sqlite3.connect")
def test_check_existing_returns_false_for_new(mock_connect):
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = None
    mock_conn.__enter__.return_value.execute.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    assert check_existing("NewTool") is False


@patch("urllib.request.urlopen")
def test_discover_handles_network_error(mock_urlopen):
    # Simulate a network error
    mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

    # Run the function, it should not raise an exception, but handle it gracefully
    tools = fetch_awesome_security_list()

    # Assert tools is an empty list as we handle it gracefully
    assert tools == []

    # Also discover_new_tools should be able to run
    result = discover_new_tools(dry_run=True)
    assert result["scanned"] == 0
    assert (
        result["errors"] == 0
    )  # we handled it in fetch_awesome_security_list so errors is 0
