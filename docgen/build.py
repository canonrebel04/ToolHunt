"""Assemble a Tier 1 doc from help text + tldr + package install commands."""
from __future__ import annotations

import re

from .helpparse import flags_in_command, known_flag_names, parse_help
from .schema import empty_doc

_HIGHLIGHT_SKIP = re.compile(r"^(help|version|v|h)$", re.IGNORECASE)


def _install_entries(cmds: list[str], method_hint: str = "") -> list[dict]:
    out = []
    for cmd in cmds:
        method = method_hint
        low = cmd.lower()
        if not method:
            if "apt " in low or "apt-get " in low:
                method = "apt"
            elif "pacman " in low or "yay " in low:
                method = "pacman"
            elif "brew " in low:
                method = "brew"
            elif "pip " in low or "pipx " in low:
                method = "pip"
            elif "cargo " in low:
                method = "cargo"
            elif "go install" in low or "go get" in low:
                method = "go"
            elif "npm " in low or "npx " in low:
                method = "npm"
            else:
                method = "shell"
        out.append({"method": method, "cmd": cmd})
    return out


def _highlights(flags: list[dict], limit: int = 8) -> list[str]:
    picks = []
    for f in flags:
        key = (f.get("name") or "").lstrip("-")
        if _HIGHLIGHT_SKIP.match(key) or not f.get("description"):
            continue
        label = f.get("short") or f["name"]
        picks.append(f"{label} — {f['description'][:90]}")
        if len(picks) >= limit:
            break
    return picks


def _validate_examples(examples: list[dict], known: set[str]) -> list[dict]:
    """Drop an example whose flags aren't in the parsed help (when help is present)."""
    if not known:
        return examples
    kept = []
    for ex in examples:
        used = flags_in_command(ex.get("cmd") or "")
        if used and not all(u in known for u in used):
            continue
        kept.append(ex)
    return kept


def from_help(tool_id: str, name: str, help_text: str, *, binary: str = "",
              install: list[str] | None = None, tldr: dict | None = None,
              description: str = "", help_source: str = "help") -> dict:
    """Build a Tier 1 doc. ``help_text`` may be empty (tldr-only / description-only)."""
    doc = empty_doc(tool_id, name)
    parsed = parse_help(help_text, binary or name) if help_text else {"usage": "", "flags": [], "subcommands": []}
    keep = ("name", "short", "aliases", "arg", "required", "description", "default", "example")
    doc["flags"] = [{k: f.get(k, [] if k == "aliases" else (False if k == "required" else "")) for k in keep}
                    for f in parsed["flags"]]
    doc["subcommands"] = parsed["subcommands"]
    doc["usage"] = parsed["usage"]
    if help_text:
        if help_source:
            doc["sources"].append(help_source)
        doc["verified"]["flags_from_help"] = True

    if install:
        doc["install"] = _install_entries(install)
        doc["sources"].append("package-install")

    examples = []
    if tldr:
        for ex in tldr.get("examples") or []:
            examples.append({**ex, "source": f"tldr:{tldr.get('name') or name}"})
        if tldr.get("description") and not description:
            description = tldr["description"]
        doc["sources"].append(f"tldr:{tldr.get('path') or tldr.get('name') or name}")
        doc["verified"]["examples_from_tldr"] = bool(tldr.get("examples"))

    known = known_flag_names(doc["flags"])
    doc["examples"] = _validate_examples(examples, known) if known else examples
    # If help is present but every tldr example used unknown flags, keep them
    # tagged as unverified rather than dropping a useful page entirely.
    if tldr and examples and not doc["examples"]:
        for ex in examples:
            doc["examples"].append({**ex, "verified": False})
        doc["verified"]["examples_from_tldr"] = False

    doc["summary"] = (description or "").strip()
    if not doc["summary"] and tldr:
        doc["summary"] = tldr.get("description") or ""
    doc["highlights"] = _highlights(doc["flags"])
    return doc


def brew_install(name: str) -> list[str]:
    return [f"brew install {name}"]


def apt_install(name: str) -> list[str]:
    return [f"sudo apt install {name}"]
