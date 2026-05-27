import urllib.request
import urllib.error
import re
import sqlite3
import time
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def fetch_awesome_security_list():
    """Fetches and parses the awesome-security list to extract tool entries."""
    url = "https://raw.githubusercontent.com/sbilly/awesome-security/master/README.md"
    tools = []

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        logger.error(f"Failed to fetch awesome-security list: {e}")
        return tools

    # Regex to match "- [Name](URL) - Description"
    pattern = re.compile(r"^\s*-\s*\[([^\]]+)\]\(([^)]+)\)(?:\s*(?:-|–)\s*(.*))?$")

    for line in content.splitlines():
        match = pattern.match(line)
        if match:
            name, link, description = match.groups()

            # Skip internal anchors
            if link.startswith("#"):
                continue

            tools.append(
                {
                    "name": name.strip(),
                    "description": description.strip() if description else "",
                    "url": link.strip(),
                }
            )

    return tools


def check_existing(name):
    """Check if a tool already exists in the database (by name, case-insensitive)."""
    db_path = "backend/database/tools.db"
    try:
        with sqlite3.connect(db_path) as conn:
            # We use LOWER(name) to ensure case-insensitive matching.
            result = conn.execute(
                "SELECT 1 FROM tools WHERE LOWER(name) = LOWER(?)", (name,)
            ).fetchone()
            return result is not None
    except sqlite3.Error as e:
        logger.error(f"Database error while checking existence of {name}: {e}")
        return False


import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from update_database import DatabaseUpdater
import sys


def discover_new_tools(dry_run=False, sources=None):
    """Run configured sources, deduplicate against existing DB, add new tools."""
    stats = {
        "scanned": 0,
        "added": 0,
        "skipped_duplicates": 0,
        "errors": 0,
        "sources": {},
    }

    available_sources = {"awesome-security": fetch_awesome_security_list}

    if sources is None:
        sources = list(available_sources.keys())

    updater = None if dry_run else DatabaseUpdater()

    for source in sources:
        if source not in available_sources:
            continue

        stats["sources"][source] = {"found": 0, "added": 0, "duplicates": 0}

        try:
            tools = available_sources[source]()
            stats["sources"][source]["found"] = len(tools)
            stats["scanned"] += len(tools)

            for tool in tools:
                if check_existing(tool["name"]):
                    stats["sources"][source]["duplicates"] += 1
                    stats["skipped_duplicates"] += 1
                    continue

                if not dry_run:
                    try:
                        updater.update_db(
                            name=tool["name"],
                            description=tool["description"],
                            url=tool["url"],
                            check_duplicate=True,  # Will double check, but we did a quick check already
                            invalidate_faiss=False,  # Don't rebuild index on every tool
                        )
                    except Exception as e:
                        logger.error(f"Error adding {tool['name']}: {e}")
                        stats["errors"] += 1
                        continue

                stats["sources"][source]["added"] += 1
                stats["added"] += 1

                # Polite delay if actually updating DB to not hammer anything (though this is local DB updates mainly here,
                # but good practice as mentioned in edge cases "rate limiting from GitHub" - but we only fetch the markdown once.
                # Just sleep a bit anyway if doing real inserts to not block things if it was a real API)
                if not dry_run:
                    time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error processing source {source}: {e}")
            stats["errors"] += 1

    # Once done, if we added tools, might want to rebuild FAISS, but instruction doesn't explicitly mandate rebuilding here,
    # and update_db handles it if invalidate_faiss=True. We skipped it per-tool to be fast. We could do it at the end.
    if not dry_run and stats["added"] > 0:
        updater.remove_faiss_embeddings()  # Force a rebuild next time it's needed

    return stats


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    print(f"Starting Tool Discovery (Dry Run: {dry_run})...")
    result = discover_new_tools(dry_run=dry_run)
    print(f"\nTool Discovery Report:")
    print(f"  Scanned: {result['scanned']}")
    print(f"  Added:   {result['added']}")
    print(f"  Skipped: {result['skipped_duplicates']}")
    print(f"  Errors:  {result['errors']}")
    for source, source_stats in result["sources"].items():
        print(
            f"  [{source}] Found: {source_stats['found']}, Added: {source_stats['added']}, Dupes: {source_stats['duplicates']}"
        )
