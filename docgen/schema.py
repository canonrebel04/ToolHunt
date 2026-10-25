"""Doc JSON schema (shared by Tier 1 parser and Tier 2 AI enrichment)."""
from __future__ import annotations

import json
import os
from pathlib import Path

SCHEMA_VERSION = 1


def empty_doc(tool_id: str, name: str = "") -> dict:
    return {
        "id": tool_id,
        "name": name or tool_id,
        "schema_version": SCHEMA_VERSION,
        "summary": "",
        "highlights": [],
        "install": [],
        "usage": "",
        "subcommands": [],
        "flags": [],
        "examples": [],
        "see_also": [],
        "sources": [],
        "verified": {"flags_from_help": False, "examples_from_tldr": False},
    }


def docs_dir() -> Path:
    return Path(os.environ.get("TOOLHUNT_DOCS_DIR", Path(__file__).resolve().parent.parent / "data" / "docs"))


def doc_path(tool_id: str, root: Path | None = None) -> Path:
    return (root or docs_dir()) / f"{tool_id}.json"


def load_doc(tool_id: str, root: Path | None = None) -> dict | None:
    p = doc_path(tool_id, root)
    if not p.is_file():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_doc(doc: dict, root: Path | None = None) -> Path:
    root = root or docs_dir()
    root.mkdir(parents=True, exist_ok=True)
    p = doc_path(doc["id"], root)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return p
