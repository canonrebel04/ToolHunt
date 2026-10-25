"""Explainshell-style annotation of a CLI command against a Tier-1 doc."""

from __future__ import annotations

import re
import shlex
from typing import Any

_FLAG_RE = re.compile(r"^(-[A-Za-z0-9]+|--[A-Za-z0-9][\w-]*)(?:=(.*))?$")


def _flag_lookup(flags: list[dict]) -> dict[str, dict]:
    """Map every known spelling (long, short, aliases) to its flag record."""
    out: dict[str, dict] = {}
    for f in flags or []:
        if not isinstance(f, dict):
            continue
        names = []
        for key in ("name", "short"):
            v = (f.get(key) or "").strip()
            if v:
                names.append(v)
        for a in f.get("aliases") or []:
            if isinstance(a, str) and a.strip():
                names.append(a.strip())
        for n in names:
            out.setdefault(n, f)
    return out


def tokenize(command: str) -> list[str]:
    """Split a command line into tokens; fall back to whitespace on parse errors."""
    command = (command or "").strip()
    if not command:
        return []
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def explain_command(command: str, doc: dict[str, Any] | None) -> dict[str, Any]:
    """Annotate each token of ``command`` using ``doc``'s flags/subcommands.

    Returns a JSON-serialisable dict::

        {
          "command": "...",
          "tokens": [
            {"token": "nmap", "kind": "binary", "note": "tool binary"},
            {"token": "-sV", "kind": "flag", "note": "Probe open ports...", "flag": {...}},
            {"token": "example.com", "kind": "arg", "note": "positional argument"},
          ],
          "unknown_flags": ["--nope"],
        }
    """
    tokens = tokenize(command)
    flags = (doc or {}).get("flags") or []
    lookup = _flag_lookup(flags)
    sub_names = {
        (s.get("name") if isinstance(s, dict) else str(s)).strip()
        for s in ((doc or {}).get("subcommands") or [])
        if (s.get("name") if isinstance(s, dict) else str(s))
    }
    sub_desc = {
        s["name"]: (s.get("description") or "")
        for s in ((doc or {}).get("subcommands") or [])
        if isinstance(s, dict) and s.get("name")
    }

    annotated: list[dict[str, Any]] = []
    unknown: list[str] = []
    expect_arg_for: dict | None = None

    for i, tok in enumerate(tokens):
        if i == 0:
            annotated.append({
                "token": tok,
                "kind": "binary",
                "note": (doc or {}).get("name") or "tool binary",
            })
            continue

        if expect_arg_for is not None:
            annotated.append({
                "token": tok,
                "kind": "flag_arg",
                "note": f"argument for {expect_arg_for.get('name') or expect_arg_for.get('short')}",
                "flag": {
                    "name": expect_arg_for.get("name", ""),
                    "short": expect_arg_for.get("short", ""),
                    "description": expect_arg_for.get("description", ""),
                },
            })
            expect_arg_for = None
            continue

        m = _FLAG_RE.match(tok)
        if m:
            spelling, inline = m.group(1), m.group(2)
            # bundled short flags like -sVCnv: try whole first, else first char
            hit = lookup.get(spelling)
            if hit is None and spelling.startswith("-") and not spelling.startswith("--") and len(spelling) > 2:
                # annotate each char separately if all known; else treat as one unknown
                chars = list(spelling[1:])
                if all(lookup.get(f"-{c}") for c in chars):
                    for c in chars:
                        f = lookup[f"-{c}"]
                        annotated.append({
                            "token": f"-{c}",
                            "kind": "flag",
                            "note": f.get("description") or f.get("name") or f"-{c}",
                            "flag": {
                                "name": f.get("name", ""),
                                "short": f.get("short", ""),
                                "description": f.get("description", ""),
                                "arg": f.get("arg", ""),
                                "section": f.get("section", ""),
                            },
                        })
                    continue
            if hit is None:
                unknown.append(spelling)
                annotated.append({
                    "token": tok,
                    "kind": "unknown_flag",
                    "note": "not found in verified help output",
                })
                continue
            note = hit.get("description") or hit.get("name") or spelling
            entry = {
                "token": tok,
                "kind": "flag",
                "note": note,
                "flag": {
                    "name": hit.get("name", ""),
                    "short": hit.get("short", ""),
                    "description": hit.get("description", ""),
                    "arg": hit.get("arg", ""),
                    "section": hit.get("section", ""),
                },
            }
            annotated.append(entry)
            if inline is None and (hit.get("arg") or "").strip():
                expect_arg_for = hit
            continue

        if tok in sub_names:
            annotated.append({
                "token": tok,
                "kind": "subcommand",
                "note": sub_desc.get(tok) or "subcommand",
            })
            continue

        annotated.append({
            "token": tok,
            "kind": "arg",
            "note": "positional argument",
        })

    return {
        "command": command.strip(),
        "tokens": annotated,
        "unknown_flags": unknown,
    }
