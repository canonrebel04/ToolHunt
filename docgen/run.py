"""Generate Tier 1 docs: ``python -m docgen.run [--db PATH] [--docs-dir PATH] [--limit N]``.

Sources (no untrusted binaries are run on the host):
  * Kali tools documentation tarball — pre-captured ``root@kali:~# tool -h`` blocks
  * tldr-pages release zip (CC BY 4.0)
  * tool description + Homebrew / apt install hints from the DB
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from backend import db
from discovery.http import fetch
from discovery.sources import KALI_ARCHIVE_URL, iter_kali_archive

from . import build, kali, schema, tldr

SHOWCASE_EXAMPLES = {
    "ab-av1": [
        {"cmd": "ab-av1 auto-encode --thorough -i video-file.mkv --preset 6 --min-vmaf 95",
         "explanation": "Find a CRF that hits VMAF 95 with a thorough search, then encode",
         "source": "showcase"},
        {"cmd": "ab-av1 crf-search -i video-file.mkv --preset 6 --min-vmaf 95",
         "explanation": "Only search for the best CRF (no final encode)",
         "source": "showcase"},
    ],
}

SHOWCASE = ("nmap", "ripgrep", "ab-av1", "gobuster", "nuclei", "feroxbuster", "sqlmap",
            "hashcat", "amass", "ffuf", "hydra", "john", "jq", "fzf", "fd", "bat", "yq", "htop")


def load_captured(help_root: Path, tool_id: str) -> dict | None:
    """Optional fixtures in ``data/help/<id>/`` (meta.json + ``*.txt``)."""
    d = help_root / tool_id
    meta_f = d / "meta.json"
    if not meta_f.is_file():
        return None
    meta = json.loads(meta_f.read_text(encoding="utf-8"))
    texts = {}
    for key in meta.get("commands") or {"": ""}:
        f = d / ("root.txt" if key == "" else f"{key}.txt")
        if f.is_file():
            texts[key] = f.read_text(encoding="utf-8", errors="replace")
    return {**meta, "texts": texts}


def load_kali_index(data: bytes) -> dict[str, str]:
    return {d.lower(): md for d, md in iter_kali_archive(data)}


def match_kali(name: str, index: dict[str, str]) -> str | None:
    key = name.lower()
    if key in index:
        return index[key]
    return index.get(db.slugify(name))


_TLDR_ALIASES = {"ripgrep": "rg", "neovim": "nvim", "kubernetes-cli": "kubectl", "the_silver_searcher": "ag"}


def match_tldr(name: str, pages: dict, aliases=()) -> dict | None:
    for key in [name.lower(), *(_TLDR_ALIASES.get(name.lower(), ""),), *[a.lower() for a in aliases]]:
        if not key:
            continue
        if key in pages:
            return pages[key]
        for a in (key.removesuffix(".py"), key.replace("_", "-")):
            if a in pages:
                return pages[a]
    return None


def generate(conn, docs_root: Path, *, kali_data: bytes | None, tldr_data: bytes | None,
             limit: int | None, only: set[str] | None, log=print) -> dict:
    tools = db.load_tools(conn)
    if only:
        tools = [t for t in tools if t["id"] in only or t["name"].lower() in only]
    kali_index = load_kali_index(kali_data) if kali_data else {}
    pages = tldr.load_pages(tldr_data) if tldr_data else {}
    help_root = docs_root.parent / "help" if docs_root.name == "docs" else Path("data/help")
    stats = {"written": 0, "with_flags": 0, "with_examples": 0, "skipped": 0, "showcase": []}

    for tool in tools:
        if limit is not None and stats["written"] >= limit:
            break
        md = match_kali(tool["name"], kali_index)
        blocks = kali.help_blocks(md) if md else []
        block = kali.best_block(blocks, tool["name"]) if blocks else None
        install = kali.install_commands(md, tool["name"]) if md else []
        if not install:
            srcs = tool.get("sources") or []
            if "homebrew" in srcs or "showcase" in srcs:
                # Prefer brew for general showcase tools; apt for security.
                install = (build.brew_install(tool["name"]) if tool.get("category") == "general"
                           else build.apt_install(tool["name"]))
            elif any(s in ("kali", "blackarch") for s in srcs):
                install = build.apt_install(tool["name"])
        aliases = [r[0] for r in conn.execute(
            "SELECT alias FROM tool_aliases WHERE tool_id = ?", (tool["id"],)).fetchall()]
        page = match_tldr(tool["name"], pages, aliases) or match_tldr(tool["id"], pages, aliases)

        captured = load_captured(help_root, tool["id"])
        help_text = block["output"] if block else ""
        help_source = "kali-help" if block else ""
        if not help_text and captured and captured["texts"].get(""):
            help_text = captured["texts"][""]
            help_source = "captured-help"
        is_showcase = tool["id"] in SHOWCASE or tool["name"].lower() in SHOWCASE
        if not help_text and not page and not install and not is_showcase:
            stats["skipped"] += 1
            continue

        binary = ((captured or {}).get("binary") or (block or {}).get("binary") or tool["name"])
        doc = build.from_help(
            tool["id"], tool["name"], help_text,
            binary=binary, install=install, tldr=page,
            description=tool.get("description") or "", help_source=help_source,
        )
        # Merge subcommand help fixtures (e.g. ab-av1 auto-encode).
        if captured:
            for sub, text in captured["texts"].items():
                if not sub:
                    continue
                sub_parsed = build.from_help(tool["id"], tool["name"], text,
                                             binary=f"{binary} {sub}", help_source="captured-help")
                existing = {f["name"] for f in doc["flags"]}
                for f in sub_parsed["flags"]:
                    if f["name"] in existing and f["name"] in ("--help", "-h", "--version", "-V"):
                        continue
                    f["section"] = sub
                    doc["flags"].append(f)
                    existing.add(f["name"])
                if not any(s["name"] == sub for s in doc["subcommands"]):
                    doc["subcommands"].append({"name": sub, "description": ""})
            if "captured-help" not in doc["sources"] and any(captured["texts"].values()):
                doc["sources"].append("captured-help")

        if not doc["flags"] and not doc["examples"] and not doc["install"] and not is_showcase:
            stats["skipped"] += 1
            continue
        stats["written"] += 1
        stats["with_flags"] += bool(doc["flags"])
        stats["with_examples"] += bool(doc["examples"])
        for ex in SHOWCASE_EXAMPLES.get(tool["id"], []):
            if not any(e.get("cmd") == ex["cmd"] for e in doc["examples"]):
                doc["examples"].append(ex)
        schema.save_doc(doc, docs_root)
        if is_showcase:
            stats["showcase"].append(tool["id"])
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--db", default=None)
    ap.add_argument("--docs-dir", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--only", default="", help="comma-separated tool ids/names")
    ap.add_argument("--skip-kali", action="store_true")
    ap.add_argument("--skip-tldr", action="store_true")
    ap.add_argument("--kali-cache", default=None)
    ap.add_argument("--tldr-cache", default=None)
    ap.add_argument("--report", default=None)
    args = ap.parse_args(argv)

    docs_root = Path(args.docs_dir) if args.docs_dir else schema.docs_dir()
    only = {x.strip().lower() for x in args.only.split(",") if x.strip()} or None

    kali_data = None
    if not args.skip_kali:
        if args.kali_cache and Path(args.kali_cache).is_file():
            kali_data = Path(args.kali_cache).read_bytes()
        else:
            print("fetching Kali tools archive…", file=sys.stderr)
            kali_data = fetch(KALI_ARCHIVE_URL, timeout=180)
            if args.kali_cache:
                Path(args.kali_cache).write_bytes(kali_data)

    tldr_data = None
    if not args.skip_tldr:
        if args.tldr_cache and Path(args.tldr_cache).is_file():
            tldr_data = Path(args.tldr_cache).read_bytes()
        else:
            print("fetching tldr pages…", file=sys.stderr)
            tldr_data = fetch(tldr.TLDR_ZIP_URL, timeout=120)
            if args.tldr_cache:
                Path(args.tldr_cache).write_bytes(tldr_data)

    conn = db.connect(args.db)
    try:
        stats = generate(conn, docs_root, kali_data=kali_data, tldr_data=tldr_data,
                         limit=args.limit, only=only)
    finally:
        conn.close()

    report = {"docs_dir": str(docs_root), **stats}
    print(json.dumps(report, indent=2))
    if args.report:
        Path(args.report).write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
