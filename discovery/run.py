"""Run discovery: ``python -m discovery.run [--sources a,b] [--db PATH] [--report FILE] [--dry-run]``.

Collects candidates from every source, enriches GitHub repos, applies quality
gates to new tools, and upserts into the SQLite DB. Writes a Markdown summary
(used as the weekly PR body).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict

from backend import db

from . import quality, sources
from .github_meta import fetch_repo_meta


def merge_candidates(cands: list[dict]) -> list[dict]:
    """Collapse duplicates within one run (same slug): union sources/tags, security wins."""
    merged: dict[str, dict] = {}
    for c in cands:
        key = db.slugify(c.get("name") or "")
        if not key:
            continue
        cur = merged.get(key)
        if cur is None:
            merged[key] = {**c, "sources": list(c.get("sources") or []), "tags": list(c.get("tags") or []),
                           "aliases": list(c.get("aliases") or [])}
            continue
        for f in ("sources", "tags", "aliases"):
            cur[f] = list(dict.fromkeys([*cur[f], *(c.get(f) or [])]))
        for f, v in c.items():
            if f not in ("sources", "tags", "aliases", "category") and v and not cur.get(f):
                cur[f] = v
        if c.get("category") == "security":
            cur["category"] = "security"
    return list(merged.values())


def apply_meta(cand: dict, meta: dict | None) -> dict:
    if not meta:
        return cand
    out = dict(cand)
    for f in ("stars", "last_commit", "language", "license", "archived"):
        if meta.get(f) not in (None, ""):
            out[f] = meta[f]
    if not out.get("description") and meta.get("repo_description"):
        out["description"] = meta["repo_description"]
    return out


def run(source_names, conn, *, max_new: int = 1500, log=print) -> dict:
    stats = {"per_source": {}, "errors": {}, "rejected": Counter(), "new": [], "updated": 0}
    raw = []
    for name in source_names:
        try:
            got = sources.COLLECTORS[name]()
            stats["per_source"][name] = len(got)
            raw.extend(got)
            log(f"{name}: {len(got)} candidates")
        except Exception as e:  # noqa: BLE001 - a dead source must not block the others
            stats["errors"][name] = f"{type(e).__name__}: {e}"
            log(f"{name}: FAILED {e}")
    cands = merge_candidates(raw)

    existing_repos = [r[0] for r in conn.execute("SELECT repo_url FROM tools WHERE repo_url != ''")]
    cand_repos = [db.canonical_repo_url(c.get("repo_url") or c.get("url") or "") for c in cands]
    meta = fetch_repo_meta([*existing_repos, *cand_repos], log=log)
    stats["enriched"] = len(meta)

    before = {r[0]: r[1] for r in conn.execute("SELECT id, updated_at FROM tools")}
    fresh = []
    for c, repo in zip(cands, cand_repos, strict=True):
        m = meta.get(repo)
        if db.find_existing(conn, c["name"], repo, c.get("aliases") or ()) is not None:
            db.upsert_tool(conn, apply_meta(c, m), c.get("aliases") or ())
            continue
        why = quality.reject_reason(c, m)
        if why:
            stats["rejected"][why] += 1
        else:
            fresh.append((quality.score(m, c.get("sources") or []), c, m))
    # Best-scored first, so the per-run cap keeps the strongest candidates.
    fresh.sort(key=lambda x: -x[0])
    for score, c, m in fresh:
        if len(stats["new"]) >= max_new:
            stats["rejected"]["over-cap (next run)"] += 1
            continue
        tool = {**apply_meta(c, m), "quality": score}
        tid, created = db.upsert_tool(conn, tool, c.get("aliases") or ())
        if created:
            stats["new"].append((tid, tool["name"], tool["category"], tool.get("subcategory") or "",
                                 ",".join(tool.get("sources") or [])))

    # Refresh GitHub metadata for tools no source mentioned this run.
    for tid, repo in conn.execute("SELECT id, repo_url FROM tools WHERE repo_url != ''").fetchall():
        m = meta.get(repo)
        if m:
            upd = {f: m[f] for f in ("stars", "last_commit", "archived")}
            upd["archived"] = int(bool(upd["archived"]))
            row = conn.execute("SELECT stars, last_commit, archived, language, license FROM tools WHERE id = ?",
                               (tid,)).fetchone()
            for f in ("language", "license"):
                if m.get(f) and not row[f]:
                    upd[f] = m[f]
            if any(row[k] != v for k, v in upd.items()):
                upd["updated_at"] = db.now_iso()
                conn.execute(f"UPDATE tools SET {', '.join(f'{k} = ?' for k in upd)} WHERE id = ?",
                             (*upd.values(), tid))
    after = {r[0]: r[1] for r in conn.execute("SELECT id, updated_at FROM tools")}
    stats["updated"] = sum(1 for k, v in after.items() if k in before and before[k] != v)
    stats["total"] = len(after)
    stats["by_category"] = dict(conn.execute("SELECT category, count(*) FROM tools GROUP BY category").fetchall())
    return stats


def report_md(stats: dict) -> str:
    lines = ["## Weekly tool discovery", ""]
    lines.append(f"**{len(stats['new'])} new tools**, {stats['updated']} existing tools refreshed "
                 f"(stars / last commit / archived), {stats.get('enriched', 0)} GitHub repos checked.")
    lines.append(f"Total now: {stats['total']} ({', '.join(f'{k}: {v}' for k, v in sorted(stats['by_category'].items()))}).")
    lines += ["", "| Source | Candidates |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in stats["per_source"].items()]
    for k, v in stats["errors"].items():
        lines.append(f"| {k} | ⚠️ failed: {v[:120]} |")
    if stats["rejected"]:
        lines += ["", "Skipped new candidates: " + ", ".join(f"{k} {v}" for k, v in stats["rejected"].most_common())]
    if stats["new"]:
        by_cat = defaultdict(list)
        for row in stats["new"]:
            by_cat[row[2]].append(row)
        for cat, rows in sorted(by_cat.items()):
            lines += ["", f"<details><summary>New {cat} tools ({len(rows)})</summary>", "",
                      "| Tool | Subcategory | Sources |", "|---|---|---|"]
            lines += [f"| {r[1].replace('|', '/')} | {r[3]} | {r[4]} |" for r in rows[:400]]
            if len(rows) > 400:
                lines.append(f"| … {len(rows) - 400} more | | |")
            lines += ["", "</details>"]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sources", default=",".join(sources.COLLECTORS))
    ap.add_argument("--db", default=None, help="SQLite path (default: TOOLHUNT_DB or backend/database/tools.db)")
    ap.add_argument("--report", default=None, help="write Markdown summary here")
    ap.add_argument("--max-new", type=int, default=1500)
    ap.add_argument("--dry-run", action="store_true", help="roll back instead of committing")
    args = ap.parse_args(argv)
    names = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = set(names) - set(sources.COLLECTORS)
    if unknown:
        ap.error(f"unknown sources: {', '.join(sorted(unknown))}")

    conn = db.connect(args.db)
    try:
        stats = run(names, conn, max_new=args.max_new)
        if len(stats["errors"]) == len(names):
            print("all sources failed", file=sys.stderr)
            return 2
        if args.dry_run:
            conn.rollback()
        else:
            conn.commit()
            conn.execute("VACUUM")
    finally:
        conn.close()
    md = report_md(stats)
    if args.report:
        with open(args.report, "w", encoding="utf-8") as f:
            f.write(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
