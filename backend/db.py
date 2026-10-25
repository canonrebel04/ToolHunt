"""SQLite data-access layer for the ToolHunt tool database.

Schema v2 (see ``SCHEMA``) replaces the original 3-column
``tools(name, description, url)`` table. ``ensure_schema()`` migrates a v1
database in place, so old copies of ``tools.db`` keep working.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = REPO_ROOT / "backend" / "database" / "tools.db"

CATEGORIES = ("security", "general")
STATUSES = ("active", "candidate", "rejected", "dead")

SCHEMA_VERSION = 2

SCHEMA = """
CREATE TABLE IF NOT EXISTS tools (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT NOT NULL DEFAULT '',
    url          TEXT NOT NULL DEFAULT '',
    repo_url     TEXT NOT NULL DEFAULT '',
    category     TEXT NOT NULL DEFAULT 'security',
    subcategory  TEXT NOT NULL DEFAULT '',
    tags         TEXT NOT NULL DEFAULT '[]',
    sources      TEXT NOT NULL DEFAULT '[]',
    language     TEXT NOT NULL DEFAULT '',
    license      TEXT NOT NULL DEFAULT '',
    stars        INTEGER,
    last_commit  TEXT NOT NULL DEFAULT '',
    archived     INTEGER NOT NULL DEFAULT 0,
    status       TEXT NOT NULL DEFAULT 'active',
    quality      REAL NOT NULL DEFAULT 0,
    first_seen   TEXT NOT NULL DEFAULT '',
    updated_at   TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category);
CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE TABLE IF NOT EXISTS tool_aliases (
    alias   TEXT PRIMARY KEY,
    tool_id TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""

JSON_FIELDS = ("tags", "sources")


def db_path() -> Path:
    """Database path, overridable with the ``TOOLHUNT_DB`` env var (used by tests)."""
    return Path(os.environ.get("TOOLHUNT_DB", DEFAULT_DB_PATH))


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def slugify(name: str) -> str:
    """Stable tool id: lowercase, alnum plus ``-``/``_``/``.``."""
    s = re.sub(r"[^a-z0-9._+-]+", "-", (name or "").strip().lower())
    return s.strip("-.") or "tool"


def connect(path: str | os.PathLike | None = None) -> sqlite3.Connection:
    p = Path(path) if path else db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    return conn


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


def ensure_schema(conn: sqlite3.Connection) -> None:
    """Create the v2 schema, migrating a v1 ``tools(name, description, url)`` table.

    No-op (no writes) when the database is already at the current version.
    """
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
        if row and row[0] == str(SCHEMA_VERSION):
            return
    except sqlite3.OperationalError:
        pass
    cols = _columns(conn, "tools")
    if cols and "id" not in cols:
        _migrate_v1(conn)
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT OR REPLACE INTO meta(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def _migrate_v1(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT name, description, url FROM tools").fetchall()
    conn.execute("ALTER TABLE tools RENAME TO tools_v1")
    conn.executescript(SCHEMA)
    ts = now_iso()
    seen: set[str] = set()
    for name, desc, url in rows:
        tid = _unique_id(slugify(name), seen)
        seen.add(tid)
        url = (url or "").strip()
        conn.execute(
            "INSERT INTO tools(id, name, description, url, repo_url, category, sources, status, first_seen, updated_at)"
            " VALUES (?, ?, ?, ?, ?, 'security', '[\"legacy\"]', 'active', ?, ?)",
            (tid, (name or "").strip(), (desc or "").strip(), url,
             canonical_repo_url(url), ts, ts),
        )
    conn.execute("DROP TABLE tools_v1")


def _unique_id(base: str, taken: set[str]) -> str:
    tid, n = base, 2
    while tid in taken:
        tid, n = f"{base}-{n}", n + 1
    return tid


def canonical_repo_url(url: str) -> str:
    """Return ``https://github.com/owner/repo`` (lowercased) for GitHub/GitLab URLs, else ''."""
    m = re.match(r"^(?:https?://)?(?:www\.)?(github\.com|gitlab\.com|codeberg\.org)/([^/\s#?]+)/([^/\s#?]+)",
                 (url or "").strip(), re.IGNORECASE)
    if not m:
        return ""
    host, owner, repo = m.groups()
    repo = re.sub(r"\.git$", "", repo)
    return f"https://{host.lower()}/{owner.lower()}/{repo.lower()}"


def row_to_dict(row: sqlite3.Row) -> dict:
    d = dict(row)
    for f in JSON_FIELDS:
        try:
            d[f] = json.loads(d.get(f) or "[]")
        except (TypeError, ValueError):
            d[f] = []
    return d


def load_tools(conn: sqlite3.Connection, status: str = "active") -> list[dict]:
    rows = conn.execute("SELECT * FROM tools WHERE status = ? ORDER BY rowid", (status,)).fetchall()
    return [row_to_dict(r) for r in rows]


def get_tool(conn: sqlite3.Connection, tool_id: str) -> dict | None:
    row = conn.execute("SELECT * FROM tools WHERE id = ?", (tool_id,)).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT t.* FROM tool_aliases a JOIN tools t ON t.id = a.tool_id WHERE a.alias = ?",
            (tool_id.lower(),),
        ).fetchone()
    return row_to_dict(row) if row else None


def find_existing(conn: sqlite3.Connection, name: str, repo_url: str = "", aliases=()) -> str | None:
    """Dedup lookup: slug/name/alias first, then canonical repo URL.

    The repo URL is only used when exactly one tool has it and the repo name
    matches one side (``rg`` -> ripgrep repo -> tool ``ripgrep``). Some repos
    ship several tools (e.g. dirkjanm/roadtools), and those must stay separate.
    """
    for a in [name, *aliases]:
        a = slugify(a)
        r = conn.execute("SELECT id FROM tools WHERE id = ? OR lower(name) = ?", (a, a)).fetchone()
        if r:
            return r[0]
        r = conn.execute("SELECT tool_id FROM tool_aliases WHERE alias = ?", (a,)).fetchone()
        if r:
            return r[0]
    repo = canonical_repo_url(repo_url)
    if repo:
        rows = conn.execute("SELECT id FROM tools WHERE repo_url = ? LIMIT 2", (repo,)).fetchall()
        base = slugify(repo.rsplit("/", 1)[-1])
        names = {slugify(n) for n in [name, *aliases]}
        if len(rows) == 1 and (rows[0][0] == base or base in names):
            return rows[0][0]
    return None


UPDATABLE = ("description", "url", "repo_url", "subcategory", "language", "license",
             "stars", "last_commit", "archived")


def upsert_tool(conn: sqlite3.Connection, tool: dict, aliases=()) -> tuple[str, bool]:
    """Insert or merge a tool. Returns ``(id, created)``.

    Merge rules: sources/tags are unioned; empty fields are filled; stars and
    last_commit are refreshed; category is never downgraded from 'security'.
    """
    name = (tool.get("name") or "").strip()
    if not name:
        raise ValueError("Tool name cannot be empty or whitespace-only.")
    repo = canonical_repo_url(tool.get("repo_url") or tool.get("url") or "")
    ts = now_iso()
    existing_id = find_existing(conn, name, repo, aliases)
    if existing_id:
        cur = row_to_dict(conn.execute("SELECT * FROM tools WHERE id = ?", (existing_id,)).fetchone())
        upd = {}
        for f in UPDATABLE:
            v = tool.get(f)
            if f == "repo_url":
                v = repo
            if v in (None, ""):
                continue
            if (f in ("stars", "last_commit", "archived") or not cur.get(f)) and v != cur.get(f):
                upd[f] = v
        for f in JSON_FIELDS:
            merged = list(dict.fromkeys([*cur[f], *(tool.get(f) or [])]))
            if merged != cur[f]:
                upd[f] = json.dumps(merged)
        if tool.get("category") == "security" and cur["category"] != "security":
            upd["category"] = "security"
        if upd:
            upd["updated_at"] = ts
            sets = ", ".join(f"{k} = ?" for k in upd)
            conn.execute(f"UPDATE tools SET {sets} WHERE id = ?", (*upd.values(), existing_id))
        _add_aliases(conn, existing_id, aliases)
        return existing_id, False

    taken = {r[0] for r in conn.execute("SELECT id FROM tools")}
    tid = _unique_id(slugify(tool.get("id") or name), taken)
    category = tool.get("category") or "security"
    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {CATEGORIES}")
    conn.execute(
        "INSERT INTO tools(id, name, description, url, repo_url, category, subcategory, tags, sources,"
        " language, license, stars, last_commit, archived, status, quality, first_seen, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (tid, name, (tool.get("description") or "").strip(), (tool.get("url") or repo or "").strip(), repo,
         category, tool.get("subcategory") or "", json.dumps(tool.get("tags") or []),
         json.dumps(tool.get("sources") or []), tool.get("language") or "", tool.get("license") or "",
         tool.get("stars"), tool.get("last_commit") or "", int(bool(tool.get("archived"))),
         tool.get("status") or "active", float(tool.get("quality") or 0), ts, ts),
    )
    _add_aliases(conn, tid, aliases)
    return tid, True


def _add_aliases(conn: sqlite3.Connection, tool_id: str, aliases) -> None:
    for a in aliases:
        a = slugify(a)
        if a and a != tool_id:
            conn.execute("INSERT OR IGNORE INTO tool_aliases(alias, tool_id) VALUES (?, ?)", (a, tool_id))
