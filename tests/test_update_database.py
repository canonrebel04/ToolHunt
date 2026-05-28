import pytest
from unittest.mock import patch
from update_database import DatabaseUpdater

@pytest.fixture
def temp_updater(tmp_path):
    return DatabaseUpdater(
        csv_file=str(tmp_path / "tools.csv"),
        sql_db_file=str(tmp_path / "tools.db"),
        faiss_dir=str(tmp_path / "faiss")
    )

def test_update_db_success(temp_updater):
    with patch.object(temp_updater, 'update_sql_db', return_value=True) as mock_sql, \
         patch.object(temp_updater, 'remove_faiss_embeddings') as mock_faiss:

        result = temp_updater.update_db("Test", "Desc", "http://test", check_duplicate=True, invalidate_faiss=True)

        assert result is True
        mock_sql.assert_called_once_with("Test", "Desc", "http://test", True)
        mock_faiss.assert_called_once()

def test_update_db_duplicate(temp_updater):
    with patch.object(temp_updater, 'update_sql_db', return_value=False) as mock_sql, \
         patch.object(temp_updater, 'remove_faiss_embeddings') as mock_faiss:

        result = temp_updater.update_db("Test", "Desc", "http://test", check_duplicate=True, invalidate_faiss=True)

        assert result is False
        mock_sql.assert_called_once_with("Test", "Desc", "http://test", True)
        mock_faiss.assert_called_once()

def test_update_db_no_invalidate(temp_updater):
    with patch.object(temp_updater, 'update_sql_db', return_value=True), \
         patch.object(temp_updater, 'remove_faiss_embeddings') as mock_faiss:

        result = temp_updater.update_db("Test", "Desc", "http://test", invalidate_faiss=False)

        assert result is True
        mock_faiss.assert_not_called()

def test_update_db_exception(temp_updater):
    with patch.object(temp_updater, 'update_sql_db', side_effect=Exception("DB Error")):
        with pytest.raises(Exception, match="DB Error"):
            temp_updater.update_db("Test", "Desc", "http://test")
