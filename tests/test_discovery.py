"""Offline tests for the discovery pipeline (no network)."""
import io
import tarfile
from datetime import date

import pytest

from backend import db
from discovery import quality, run, sources
from discovery.github_meta import build_query, parse_response, split_repo

KALI_MD = """---
Title: 0trace
Homepage: https://lcamtuf.coredump.cx
Repository: https://gitlab.com/kalilinux/packages/0trace
Version: 0.01-3kali4
Metapackages: kali-linux-everything kali-tools-information-gathering kali-tools-top10
PackagesInfo: |
 ### 0trace

 **Traceroute tool that can run within an existing TCP connection**
  The package is traceroute tool.

 **Installed size:** `43 KB`
 **How to install:** `sudo apt install 0trace`
---
body
"""

KALI_PLAIN = """---
Title: cherrytree
Homepage: https://www.giuspen.net/cherrytree/
Metapackages: kali-linux-everything
PackagesInfo: |
 ### cherrytree

 **Hierarchical note taking application**
---
"""

KALI_PARAGRAPH = """---
Title: dumpthing
Homepage: https://github.com/acme/dumpthing
Metapackages: kali-linux-everything
PackagesInfo: |
 ### dumpthing

  Extracts credentials from memory dumps. It is fast.

 **Installed size:** `1 KB`
---
"""

KALI_ARCHIVED = KALI_MD.replace("Title: 0trace", 'archived: "true"\nTitle: 0trace')


def test_blackarch_parse():
    text = "0d1n|1:290.2d16bc5|Web security tool for fuzzing HTTP inputs.| blackarch blackarch-webapp |https://github.com/CoolerVoid/0d1n\nbad line\n"
    (t,) = list(sources.parse_blackarch(text))
    assert t["name"] == "0d1n" and t["category"] == "security"
    assert t["subcategory"] == "Webapp" and t["tags"] == ["webapp"]
    assert t["url"] == "https://github.com/CoolerVoid/0d1n"


def test_kali_parse_metapackage():
    t = sources.parse_kali_tool(KALI_MD)
    assert t["name"] == "0trace"
    assert t["description"] == "Traceroute tool that can run within an existing TCP connection"
    assert t["category"] == "security" and t["subcategory"] == "Information Gathering"
    assert "top10" not in t["tags"]


def test_kali_skips_plain_utilities_and_archived():
    assert sources.parse_kali_tool(KALI_PLAIN) is None
    assert sources.parse_kali_tool(KALI_ARCHIVED) is None


def test_kali_paragraph_fallback_and_keyword_security():
    t = sources.parse_kali_tool(KALI_PARAGRAPH)
    assert t["description"] == "Extracts credentials from memory dumps"
    assert t["category"] == "security"
    assert t["repo_url"] == "https://github.com/acme/dumpthing"


def test_kali_archive_iter():
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path, text in [("kali-tools-main/0trace/index.md", KALI_MD), ("kali-tools-main/README.md", "x"),
                           ("kali-tools-main/0trace/images/a.md", "x")]:
            data = text.encode()
            info = tarfile.TarInfo(path)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    got = list(sources.iter_kali_archive(buf.getvalue()))
    assert [d for d, _ in got] == ["0trace"]


def test_cli_apps_parse():
    csv = "category,name,homepage,git,description\ntext-search,ripgrep,,https://github.com/BurntSushi/ripgrep,Fast grep.\n,,,,\n"
    (t,) = list(sources.parse_cli_apps(csv))
    assert t["category"] == "general" and t["subcategory"] == "Text Search"
    assert t["repo_url"] == "https://github.com/BurntSushi/ripgrep"


def test_homebrew_filters_libraries():
    analytics = {"items": [{"formula": f} for f in ["libpng", "ripgrep", "python@3.12", "hello", "openssl@3", "dep", "fmt"]]}
    formulae = [
        {"name": "libpng", "desc": "Library for PNG"},
        {"name": "ripgrep", "desc": "Search tool like grep", "homepage": "https://github.com/BurntSushi/ripgrep",
         "aliases": ["rg"], "license": "Unlicense"},
        {"name": "python@3.12", "desc": "Interpreted language"},
        {"name": "hello", "desc": "Program providing model for GNU coding standards"},
        {"name": "dep", "desc": "Go dependency tool", "deprecated": True},
        {"name": "fmt", "desc": "Open-source formatting library for C++"},
    ]
    got = list(sources.parse_homebrew(analytics, formulae))
    assert [t["name"] for t in got] == ["ripgrep"]
    assert got[0]["aliases"] == ["rg"] and got[0]["category"] == "general"


def test_github_search_filters_lists_and_forks():
    items = [
        {"name": "awesome-hacking", "description": "A curated list", "html_url": "https://github.com/a/awesome-hacking"},
        {"name": "nuclei", "description": "Fast vulnerability scanner", "html_url": "https://github.com/p/nuclei",
         "stargazers_count": 20000, "pushed_at": "2026-10-01T00:00:00Z", "license": {"spdx_id": "MIT"}, "topics": ["security"]},
        {"name": "forked", "description": "fork", "fork": True, "html_url": "https://github.com/x/forked"},
        {"name": "PayloadsAllTheThings", "description": "Cheat sheet of payloads", "html_url": "https://github.com/s/p"},
    ]
    (t,) = list(sources.parse_github_search(items, "security", "pentesting"))
    assert t["name"] == "nuclei" and t["stars"] == 20000 and t["last_commit"] == "2026-10-01"
    assert t["subcategory"] == "Pentesting" and t["license"] == "MIT"


def test_graphql_query_and_parse():
    assert split_repo("https://github.com/owner/repo") == ("owner", "repo")
    assert split_repo("https://gitlab.com/owner/repo") is None
    repos = [("o", "a"), ("o", "missing")]
    q = build_query(repos)
    assert 'r0: repository(owner: "o", name: "a")' in q and "r1:" in q
    payload = {"data": {"r0": {"stargazerCount": 5, "isArchived": True, "isFork": False, "pushedAt": "2020-01-02T00:00:00Z",
                               "licenseInfo": {"spdxId": "NOASSERTION"}, "primaryLanguage": {"name": "Go"}}, "r1": None}}
    meta = parse_response(repos, payload)
    assert meta == {"https://github.com/o/a": {"stars": 5, "archived": True, "fork": False, "last_commit": "2020-01-02",
                                               "license": "", "language": "Go", "repo_description": ""}}


@pytest.mark.parametrize(("cand", "meta", "why"), [
    ({"description": "short"}, None, "short-description"),
    ({"description": "A long enough description", "sources": ["cli-apps"], "category": "general"},
     {"stars": 50, "last_commit": "2026-01-01"}, "low-stars"),
    ({"description": "A long enough description", "sources": ["cli-apps"], "category": "general"},
     {"stars": 200, "last_commit": "2019-01-01"}, "stale"),
    ({"description": "A long enough description", "sources": ["github:cli"], "category": "general"},
     {"stars": 5000, "archived": True}, "archived"),
    ({"description": "A long enough description", "sources": ["blackarch"], "category": "security"},
     {"stars": 1, "archived": True, "last_commit": "2010-01-01"}, None),  # curated lists are trusted
    ({"description": "A long enough description", "sources": ["cli-apps"], "category": "general"},
     {"stars": 200, "last_commit": "2026-01-01"}, None),
])
def test_quality_gate(cand, meta, why):
    assert quality.reject_reason(cand, meta, today=date(2026, 10, 24)) == why


def test_merge_candidates_security_wins():
    merged = run.merge_candidates([
        {"name": "Nmap", "description": "", "category": "general", "sources": ["homebrew"], "aliases": ["nmap-cli"]},
        {"name": "nmap", "description": "Network mapper", "category": "security", "sources": ["kali"]},
    ])
    assert len(merged) == 1
    m = merged[0]
    assert m["category"] == "security" and m["description"] == "Network mapper"
    assert m["sources"] == ["homebrew", "kali"] and m["aliases"] == ["nmap-cli"]


def test_run_end_to_end(tmp_path, monkeypatch):
    path = tmp_path / "t.db"
    conn = db.connect(path)
    db.upsert_tool(conn, {"name": "nmap", "description": "Network scanner", "url": "https://nmap.org",
                          "category": "security"})
    conn.commit()
    fake = {
        "kali": lambda: [{"name": "nmap", "description": "Network mapper", "category": "security",
                          "subcategory": "Information Gathering", "sources": ["kali"], "tags": ["information-gathering"]}],
        "cli-apps": lambda: [
            {"name": "ripgrep", "description": "Fast line-oriented search tool", "url": "https://github.com/BurntSushi/ripgrep",
             "repo_url": "https://github.com/BurntSushi/ripgrep", "category": "general", "sources": ["cli-apps"]},
            {"name": "tiny", "description": "Too few stars here", "repo_url": "https://github.com/x/tiny",
             "category": "general", "sources": ["cli-apps"]},
        ],
        "broken": lambda: (_ for _ in ()).throw(OSError("down")),
    }
    monkeypatch.setattr(sources, "COLLECTORS", fake)
    meta = {"https://github.com/burntsushi/ripgrep": {"stars": 50000, "archived": False, "fork": False,
                                                      "last_commit": "2026-10-01", "license": "MIT", "language": "Rust"},
            "https://github.com/x/tiny": {"stars": 3, "archived": False, "fork": False, "last_commit": "2026-10-01"}}
    monkeypatch.setattr(run, "fetch_repo_meta", lambda urls, log=print: meta)
    stats = run.run(["kali", "cli-apps", "broken"], conn, log=lambda *a: None)
    conn.commit()
    assert [n[1] for n in stats["new"]] == ["ripgrep"]
    assert stats["rejected"]["low-stars"] == 1 and "broken" in stats["errors"]
    rg = db.get_tool(conn, "ripgrep")
    assert rg["category"] == "general" and rg["stars"] == 50000 and rg["language"] == "Rust"
    nm = db.get_tool(conn, "nmap")
    assert nm["description"] == "Network scanner"  # existing description kept
    assert nm["subcategory"] == "Information Gathering" and nm["sources"] == ["kali"]
    md = run.report_md(stats)
    assert "1 new tools" in md and "ripgrep" in md and "failed" in md
    conn.close()


def test_run_respects_cap(tmp_path, monkeypatch):
    conn = db.connect(tmp_path / "t.db")
    cands = [{"name": f"tool{i}", "description": "A security tool here", "category": "security",
              "sources": ["blackarch"]} for i in range(5)]
    monkeypatch.setattr(sources, "COLLECTORS", {"blackarch": lambda: cands})
    monkeypatch.setattr(run, "fetch_repo_meta", lambda urls, log=print: {})
    stats = run.run(["blackarch"], conn, max_new=2, log=lambda *a: None)
    assert len(stats["new"]) == 2 and stats["rejected"]["over-cap (next run)"] == 3
    conn.close()
