"""Add tools to the ToolHunt database by hand (``python update_database.py``).

Thin wrapper over :mod:`backend.db` (schema v2). The FAISS index no longer has
to be deleted after an update: the search backend notices the tool list changed
(via ``backend/faiss_index/index_meta.json``) and rebuilds the index itself.
"""
import logging
import shutil
import sqlite3
from pathlib import Path

from backend import db

logger = logging.getLogger(__name__)


class DatabaseUpdater:
    """Manages manual additions to the tool database."""

    def __init__(
        self,
        csv_file: str = "backend/database/tool_list_database.csv",
        sql_db_file: str | None = None,
        faiss_dir: str = "backend/faiss_index",
    ) -> None:
        self.csv_file = Path(csv_file)  # kept for backwards compatibility; unused
        self.sql_db_file = Path(sql_db_file) if sql_db_file else db.db_path()
        self.faiss_dir = Path(faiss_dir)
        self.sql_db_file.parent.mkdir(parents=True, exist_ok=True)
        db.connect(self.sql_db_file).close()  # create / migrate schema

    def update_sql_db(
        self,
        name: str,
        description: str,
        url: str,
        check_duplicate: bool = True,
        category: str = "security",
    ) -> bool:
        """Insert a tool. Returns False if it already exists (``check_duplicate``).

        With ``check_duplicate=False`` an existing tool with the same identity is
        updated in place instead (tool ids are unique in schema v2).
        """
        name_norm = name.strip()
        if not name_norm:
            raise ValueError("Tool name cannot be empty or whitespace-only.")
        conn = db.connect(self.sql_db_file)
        try:
            tool = {"name": name_norm, "description": description.strip(), "url": url.strip(),
                    "category": category, "sources": ["manual"]}
            existing = db.find_existing(conn, name_norm, db.canonical_repo_url(tool["url"]))
            if existing and check_duplicate:
                logger.info("Skipped duplicate tool in SQL DB: '%s'", name_norm)
                return False
            if existing:
                conn.execute(
                    "UPDATE tools SET description = ?, url = ?, updated_at = ? WHERE id = ?",
                    (tool["description"], tool["url"], db.now_iso(), existing),
                )
                conn.commit()
            else:
                db.upsert_tool(conn, tool)
                conn.commit()
        finally:
            conn.close()
        logger.debug("Saved tool into SQL DB: %s", name_norm)
        return True

    def remove_faiss_embeddings(self) -> None:
        """Remove the FAISS index directory if it exists (forces a full rebuild)."""
        if self.faiss_dir.exists():
            shutil.rmtree(self.faiss_dir)
            logger.info("Removed FAISS embeddings directory: %s", self.faiss_dir)

    def update_db(
        self,
        name: str,
        description: str,
        url: str,
        check_duplicate: bool = True,
        invalidate_faiss: bool = False,
        category: str = "security",
    ) -> bool:
        """Add a tool. ``invalidate_faiss`` is no longer needed (stale indexes rebuild automatically)."""
        try:
            added = self.update_sql_db(name, description, url, check_duplicate, category)
            if invalidate_faiss:
                self.remove_faiss_embeddings()
            return added
        except Exception:
            logger.exception("Failed to update databases for tool: %s", name)
            raise


def main() -> None:
    """Add a tool from the command line (run as a script only)."""
    import argparse

    parser = argparse.ArgumentParser(description="Add a tool to the ToolHunt database")
    parser.add_argument("name")
    parser.add_argument("description")
    parser.add_argument("url")
    parser.add_argument("--category", choices=db.CATEGORIES, default="security")
    args = parser.parse_args()
    updater = DatabaseUpdater()
    try:
        added = updater.update_db(args.name, args.description, args.url, category=args.category)
        print("Tool added successfully." if added else "Tool was a duplicate and skipped.")
    except (sqlite3.Error, OSError, ValueError) as e:
        print(f"Update failed: {e}")


if __name__ == "__main__":
    main()
