import logging
import sqlite3
from pathlib import Path
from typing import Optional
import shutil

# Configure module-level logger
logger = logging.getLogger(__name__)


class DatabaseUpdater:
    """Manages updates to tool database across SQLite and FAISS index."""

    def __init__(
        self,
        sql_db_file: str = "backend/database/tools.db",
        faiss_dir: str = "backend/faiss_index",
    ) -> None:
        self.sql_db_file = Path(sql_db_file)
        self.faiss_dir = Path(faiss_dir)

        # Ensure parent directories exist
        self.sql_db_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite connection and ensure table exists
        self._init_sql_table()

    def _init_sql_table(self) -> None:
        """Create the 'tools' table if it doesn't exist."""
        with sqlite3.connect(self.sql_db_file) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tools (
                    name TEXT NOT NULL,
                    description TEXT,
                    url TEXT
                )
            """)
            conn.commit()

    def update_sql_db(
        self,
        name: str,
        description: str,
        url: str,
        check_duplicate: bool = True,
    ) -> bool:
        """
        Insert a new tool into the SQLite database.

        Parameters
        ----------
        name : str
            Name of the tool.
        description : str
            Description of the tool.
        url : str
            URL to the tool.
        check_duplicate : bool, optional
            If True, skip insertion if a tool with the same (case-insensitive)
            name already exists. Default is True.

        Returns
        -------
        bool
            True if inserted, False if skipped due to duplication.
        """
        name_norm = name.strip()
        if not name_norm:
            raise ValueError("Tool name cannot be empty or whitespace-only.")

        with sqlite3.connect(self.sql_db_file) as conn:
            cursor = conn.cursor()

            if check_duplicate:
                cursor.execute(
                    "SELECT 1 FROM tools WHERE LOWER(name) = LOWER(?) LIMIT 1",
                    (name_norm,)
                )
                if cursor.fetchone():
                    logger.info("Skipped duplicate tool in SQL DB: '%s'", name_norm)
                    return False

            cursor.execute(
                "INSERT INTO tools (name, description, url) VALUES (?, ?, ?)",
                (name_norm, description.strip(), url.strip())
            )
            conn.commit()

        logger.debug("Inserted tool into SQL DB: %s", name_norm)
        return True

    def remove_faiss_embeddings(self) -> None:
        """Remove the FAISS index directory if it exists."""
        if self.faiss_dir.exists():
            shutil.rmtree(self.faiss_dir)
            logger.info("Removed FAISS embeddings directory: %s", self.faiss_dir)

    def update_db(
        self,
        name: str,
        description: str,
        url: str,
        check_duplicate: bool = True,
        invalidate_faiss: bool = True,
    ) -> bool:
        """
        Update database components with a new tool entry.

        Parameters
        ----------
        name : str
            Tool name.
        description : str
            Tool description.
        url : str
            Tool URL.
        check_duplicate : bool, optional
            Whether to check for duplicates in SQL. Default is True.
        invalidate_faiss : bool, optional
            Whether to remove the FAISS index to force re-embedding.
            Default is True.

        Returns
        -------
        bool
            True if the tool was added (not skipped), False if duplicate and skipped.

        Raises
        ------
        Exception
            If any operation fails (logged and re-raised).
        """
        try:
            # Attempt SQL insertion
            sql_added = self.update_sql_db(name, description, url, check_duplicate)

            # Invalidate FAISS index if requested
            if invalidate_faiss:
                self.remove_faiss_embeddings()

            return sql_added

        except Exception as e:
            logger.exception("Failed to update databases for tool: %s", name)
            raise




updater = DatabaseUpdater()
try:
    added = updater.update_db(
        name="ToolHunt",
        description="ToolHunt is an advanced search engine that helps you quickly find the right cybersecurity tool from a database of over 3,000 options. Just describe what you need in plain language, and its smart, elastic search will return the best matches for security pros, pentesters, and researchers.",
        url="https://github.com/cyberytti/ToolHunt",
        check_duplicate=True,
        invalidate_faiss=True
    )
    if added:
        print("Tool added successfully.")
    else:
        print("Tool was a duplicate and skipped.")
except Exception as e:
    print(f"Update failed: {e}")
