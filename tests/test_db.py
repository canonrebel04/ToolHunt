"""Tests for backend.db (schema v2, v1 migration, dedup/upsert)."""
import json
import sqlite3

import pytest

from backend import db


def _make_v1(path):
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE tools (name TEXT NOT NULL, description TEXT, url TEXT)")
        conn.executemany(
            "INSERT INTO tools VALUES (?, ?, ?)",
            [
                ("Nmap", "Network scanner", "https://github.com/nmap/nmap"),
                ("sqlmap", "SQL injection tool", "https://github.com/sqlmapproject/sqlmap.git"),
                ("No Url Tool", "Has no url", ""),
            ],
        )


def test_migrates_v1_in_place(tmp_path):
    p = tmp_path / "tools.db"
    _make_v1(p)
    conn = db.connect(p)
    tools = {t["id"]: t for t in db.load_tools(conn)}
    assert set(tools) == {"nmap", "sqlmap", "no-url-tool"}
    assert tools["nmap"]["name"] == "Nmap"
    assert tools["nmap"]["category"] == "security"
    assert tools["nmap"]["sources"] == ["legacy"]
    assert tools["sqlmap"]["repo_url"] == "https://github.com/sqlmapproject/sqlmap"
    assert conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "2"
    assert "tools_v1" not in {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}


def test_connect_does_not_write_when_current(tmp_path):
    p = tmp_path / "tools.db"
    db.connect(p).close()
    before = p.read_bytes()
    db.connect(p).close()
    assert p.read_bytes() == before


def test_upsert_dedups_by_repo_and_merges(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    tid, created = db.upsert_tool(conn, {"name": "ripgrep", "description": "", "category": "general",
                                         "url": "https://github.com/BurntSushi/ripgrep", "sources": ["homebrew"]})
    assert (tid, created) == ("ripgrep", True)
    tid2, created2 = db.upsert_tool(conn, {"name": "rg", "description": "fast grep", "stars": 50000,
                                           "url": "https://GitHub.com/burntsushi/ripgrep/", "sources": ["crates"]},
                                    aliases=["rg"])
    assert (tid2, created2) == ("ripgrep", False)
    t = db.get_tool(conn, "rg")  # alias lookup
    assert t["id"] == "ripgrep"
    assert t["description"] == "fast grep"
    assert t["stars"] == 50000
    assert t["sources"] == ["homebrew", "crates"]


def test_security_category_never_downgraded(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    db.upsert_tool(conn, {"name": "nmap", "category": "security"})
    db.upsert_tool(conn, {"name": "nmap", "category": "general"})
    assert db.get_tool(conn, "nmap")["category"] == "security"
    db.upsert_tool(conn, {"name": "jq", "category": "general"})
    db.upsert_tool(conn, {"name": "jq", "category": "security"})
    assert db.get_tool(conn, "jq")["category"] == "security"


def test_invalid_category_rejected(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    with pytest.raises(ValueError):
        db.upsert_tool(conn, {"name": "x", "category": "games"})


def test_unique_ids_for_colliding_slugs(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    conn.execute("INSERT INTO tools(id, name, description, url, repo_url, tags, sources, first_seen, updated_at)"
                 " VALUES ('foo', 'foo', '', '', 'https://github.com/a/foo', '[]', '[]', '', '')")
    tid, created = db.upsert_tool(conn, {"name": "foo2", "id": "foo", "url": "https://github.com/b/foo"})
    assert created and tid != "foo"


def test_row_to_dict_decodes_json(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    db.upsert_tool(conn, {"name": "a", "tags": ["x", "y"]})
    raw = conn.execute("SELECT tags FROM tools WHERE id='a'").fetchone()[0]
    assert json.loads(raw) == ["x", "y"]
    assert db.get_tool(conn, "a")["tags"] == ["x", "y"]


@pytest.mark.parametrize("url,expected", [
    ("https://github.com/Owner/Repo.git", "https://github.com/owner/repo"),
    ("http://www.github.com/o/r/tree/main/x", "https://github.com/o/r"),
    ("https://gitlab.com/g/p", "https://gitlab.com/g/p"),
    ("https://nmap.org", ""),
    ("", ""),
])
def test_canonical_repo_url(url, expected):
    assert db.canonical_repo_url(url) == expected


def test_shared_repo_does_not_merge_distinct_tools(tmp_path):
    conn = db.connect(tmp_path / "t.db")
    db.upsert_tool(conn, {"name": "roadrecon", "url": "https://github.com/dirkjanm/ROADtools"})
    db.upsert_tool(conn, {"name": "roadtx", "url": "https://github.com/dirkjanm/ROADtools"})
    _, created = db.upsert_tool(conn, {"name": "roadlib", "url": "https://github.com/dirkjanm/roadtools"})
    assert created
    assert len(db.load_tools(conn)) == 3
