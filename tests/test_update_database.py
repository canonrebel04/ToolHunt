import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from update_database import DatabaseUpdater


@pytest.fixture
def db_updater(tmp_path):
    """Fixture to provide a DatabaseUpdater with a temporary SQLite db."""
    csv_file = tmp_path / "tools.csv"
    sql_file = tmp_path / "tools.db"
    faiss_dir = tmp_path / "faiss_index"

    updater = DatabaseUpdater(
        csv_file=str(csv_file),
        sql_db_file=str(sql_file),
        faiss_dir=str(faiss_dir)
    )
    return updater

def test_update_sql_db_success(db_updater):
    """Test successful insertion of a new tool."""
    result = db_updater.update_sql_db(
        name="TestTool",
        description="A great tool.",
        url="https://example.com/testtool"
    )

    assert result is True

    with sqlite3.connect(db_updater.sql_db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, description, url FROM tools WHERE name=?", ("TestTool",))
        row = cursor.fetchone()

    assert row is not None
    assert row[0] == "TestTool"
    assert row[1] == "A great tool."
    assert row[2] == "https://example.com/testtool"

def test_update_sql_db_empty_name_raises_value_error(db_updater):
    """Test that empty or whitespace-only names raise ValueError."""
    with pytest.raises(ValueError, match="Tool name cannot be empty or whitespace-only."):
        db_updater.update_sql_db(name="", description="desc", url="url")

    with pytest.raises(ValueError, match="Tool name cannot be empty or whitespace-only."):
        db_updater.update_sql_db(name="   ", description="desc", url="url")

def test_update_sql_db_skips_duplicate(db_updater):
    """Test that duplicates are skipped when check_duplicate=True."""
    result1 = db_updater.update_sql_db(
        name="DupTool",
        description="Original desc",
        url="http://url"
    )
    assert result1 is True

    result2 = db_updater.update_sql_db(
        name="duptool",
        description="New desc",
        url="http://newurl",
        check_duplicate=True
    )

    assert result2 is False

    with sqlite3.connect(db_updater.sql_db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tools WHERE LOWER(name)='duptool'")
        count = cursor.fetchone()[0]

    assert count == 1

def test_update_sql_db_without_duplicate_check_updates_in_place(db_updater):
    """Tool ids are unique in schema v2: check_duplicate=False updates the existing row."""
    assert db_updater.update_sql_db(name="DupTool", description="Original desc", url="http://url") is True
    assert db_updater.update_sql_db(
        name="duptool", description="New desc", url="http://newurl", check_duplicate=False
    ) is True

    with sqlite3.connect(db_updater.sql_db_file) as conn:
        rows = conn.execute("SELECT description, url FROM tools WHERE LOWER(name)='duptool'").fetchall()

    assert rows == [("New desc", "http://newurl")]


def test_update_sql_db_sets_category(db_updater):
    assert db_updater.update_sql_db(name="ripgrep", description="grep", url="u", category="general")
    with sqlite3.connect(db_updater.sql_db_file) as conn:
        assert conn.execute("SELECT category FROM tools WHERE id='ripgrep'").fetchone() == ("general",)


def test_import_has_no_side_effects(tmp_path):
    """Importing update_database must not create/modify the DB or delete the FAISS index.

    Runs the import in a fresh interpreter with cwd=tmp_path, so the module's
    relative default paths would resolve inside tmp_path (never the real repo
    data) if a module-level side effect ever comes back.
    """
    repo_root = Path(__file__).resolve().parent.parent
    subprocess.run(
        [sys.executable, "-c", "import update_database"],
        cwd=tmp_path,
        env={"PYTHONPATH": str(repo_root)},
        check=True,
    )
    assert not (tmp_path / "backend").exists()
