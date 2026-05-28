import sqlite3
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

    # Verify database contents
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
    # Insert first time
    result1 = db_updater.update_sql_db(
        name="DupTool",
        description="Original desc",
        url="http://url"
    )
    assert result1 is True

    # Try inserting a duplicate (case-insensitive)
    result2 = db_updater.update_sql_db(
        name="duptool",
        description="New desc",
        url="http://newurl",
        check_duplicate=True
    )

    assert result2 is False

    # Verify database has only one entry and it's the original
    with sqlite3.connect(db_updater.sql_db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tools WHERE LOWER(name)='duptool'")
        count = cursor.fetchone()[0]

    assert count == 1

def test_update_sql_db_bypasses_duplicate_check(db_updater):
    """Test that duplicates are inserted when check_duplicate=False."""
    # Insert first time
    result1 = db_updater.update_sql_db(
        name="DupTool",
        description="Original desc",
        url="http://url"
    )
    assert result1 is True

    # Try inserting a duplicate with check_duplicate=False
    result2 = db_updater.update_sql_db(
        name="duptool",
        description="New desc",
        url="http://newurl",
        check_duplicate=False
    )

    assert result2 is True

    # Verify database has both entries
    with sqlite3.connect(db_updater.sql_db_file) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tools WHERE LOWER(name)='duptool'")
        count = cursor.fetchone()[0]

    assert count == 2
