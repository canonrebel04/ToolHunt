"""Tests for the DatabaseUpdater component."""

import pytest
from unittest.mock import patch

from update_database import DatabaseUpdater

class TestDatabaseUpdaterErrorPath:
    """Tests for error handling in DatabaseUpdater.update_db."""

    def test_update_db_raises_and_logs_exception(self, tmp_path, caplog):
        """Verify that an exception in update_sql_db is logged and re-raised."""
        # Set up a temporary database environment
        csv_file = tmp_path / "test.csv"
        sql_db_file = tmp_path / "test.db"
        faiss_dir = tmp_path / "faiss"

        updater = DatabaseUpdater(
            csv_file=str(csv_file),
            sql_db_file=str(sql_db_file),
            faiss_dir=str(faiss_dir)
        )

        # Mock update_sql_db to raise an exception
        test_exception_msg = "Simulated SQL error"

        with patch.object(updater, 'update_sql_db', side_effect=Exception(test_exception_msg)):
            # The exception should be re-raised
            with pytest.raises(Exception, match=test_exception_msg):
                updater.update_db(
                    name="TestTool",
                    description="A test tool",
                    url="http://example.com"
                )

        # The exception should also be logged
        assert "Failed to update databases for tool: TestTool" in caplog.text
        assert test_exception_msg in caplog.text
