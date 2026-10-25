"""Tier-2 LLM enrichment CLI: ``python -m docgen.enrich [options]``.

Does not invent flags — only rewrites descriptions/examples on top of Tier-1
docs already present under ``data/docs/``. Requires an API key (or a local
OpenAI-compatible server). See README "AI docs (Tier 2)".
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from docgen import schema
from docgen.llm import LLMConfig, enrich_doc, list_providers
from docgen.run import load_captured


def _load_help(tool_id: str, help_root: Path) -> str:
    cap = load_captured(help_root, tool_id)
    if not cap:
        return ""
    texts = cap.get("texts") or {}
    # Prefer root help, then concatenate a bit of subcommand help
    parts = []
    if texts.get(""):
        parts.append(texts[""])
    for k, v in texts.items():
        if k and v:
            parts.append(f"# {k}\n{v}")
        if sum(len(p) for p in parts) > 8000:
            break
    return "\n\n".join(parts)[:8000]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Enrich Tier-1 docs with a pluggable LLM")
    p.add_argument("--docs-dir", type=Path, default=None, help="Docs root (default data/docs)")
    p.add_argument("--help-dir", type=Path, default=None, help="Captured help fixtures root")
    p.add_argument("--tool", action="append", default=[], help="Tool id to enrich (repeatable)")
    p.add_argument("--limit", type=int, default=10, help="Max tools when scanning the docs dir")
    p.add_argument("--provider", default=None, help=f"One of: {', '.join(list_providers())}")
    p.add_argument("--model", default=None, help="Override TOOLHUNT_LLM_MODEL")
    p.add_argument("--dry-run", action="store_true", help="Call LLM but do not write files")
    p.add_argument("--print-config", action="store_true", help="Show resolved provider config and exit")
    p.add_argument("--list-providers", action="store_true", help="List built-in providers and exit")
    args = p.parse_args(argv)

    if args.list_providers:
        for name in list_providers():
            print(name)
        return 0

    if args.model:
        os.environ["TOOLHUNT_LLM_MODEL"] = args.model

    try:
        cfg = LLMConfig.from_env(args.provider)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.print_config:
        print(json.dumps({
            "provider": cfg.provider,
            "model": cfg.model,
            "base_url": cfg.base_url,
            "kind": cfg.kind,
            "api_key_set": bool(cfg.api_key),
        }, indent=2))
        return 0

    docs_root = args.docs_dir or schema.docs_dir()
    help_root = args.help_dir or (Path(__file__).resolve().parent.parent / "data" / "help")

    if args.tool:
        ids = [t.strip().lower() for t in args.tool if t.strip()]
    else:
        ids = sorted(p.stem for p in docs_root.glob("*.json"))[: max(0, args.limit)]

    if not ids:
        print("No tools to enrich.", file=sys.stderr)
        return 1

    ok = fail = 0
    for tid in ids:
        doc = schema.load_doc(tid, docs_root)
        if doc is None:
            print(f"skip {tid}: no Tier-1 doc")
            fail += 1
            continue
        help_text = _load_help(tid, help_root)
        try:
            enriched = enrich_doc(doc, help_text=help_text, config=cfg)
        except (RuntimeError, ValueError, TypeError, OSError, json.JSONDecodeError) as e:
            print(f"fail {tid}: {e}", file=sys.stderr)
            fail += 1
            continue
        if args.dry_run:
            print(f"dry-run {tid}: summary={enriched.get('summary', '')[:80]!r}")
        else:
            schema.save_doc(enriched, docs_root)
            print(f"wrote {tid}")
        ok += 1
    print(f"done: ok={ok} fail={fail}")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
