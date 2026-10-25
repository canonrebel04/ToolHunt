"""Heuristic parser for CLI help text (clap, argparse, cobra, getopt/GNU, nmap-style).

Only flags that literally appear in the help text are returned, which is what
makes this output the ground truth that AI write-ups are validated against.
"""
from __future__ import annotations

import re

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_FLAG = r"--?[A-Za-z0-9?#][\w.#?\-\[\]]*"
_ARG = (r"(?:[ =]?(?:<[^>\n]+>|\[[^\]\n]+\]|\{[^}\n]+\}|[A-Z][A-Z0-9_\-]*(?:\.\.\.)?)"
        r"|[ =](?:string|strings|int|uint|int32|int64|float|float64|duration|bool|stringArray|stringSlice|"
        r"intSlice|value|num|number|file|path|dir|n|port|host|url|list|count)\b)")
_SPEC = re.compile(
    rf"^(?P<indent>[ \t]{{0,12}})(?P<spec>{_FLAG}(?:{_ARG})?(?:\s*[,|/]\s*{_FLAG}(?:{_ARG})?)*)"
    rf"(?P<sep>\s{{2,}}|\s*:\s+|\t+|\s*$)(?P<desc>.*)$"
)
_FLAG_TOKEN = re.compile(rf"(?<![\w-])({_FLAG})((?:{_ARG})?)")
_HEADER = re.compile(r"^(?P<h>[A-Za-z][A-Za-z0-9 /&()_\-]{1,60}):\s*$")
_CMD_LINE = re.compile(r"^(?P<indent>\s{1,12})(?P<name>[a-z0-9][\w.\-]*)(?:,\s*[\w\-]+)*\s{2,}(?P<desc>\S.*)$")
_DEFAULT = re.compile(r"[\[(]\s*(?:default(?:s)?(?: value)?|def)\s*[:=]?\s*([^\])]+?)\s*[\])]", re.IGNORECASE)
_REQUIRED = re.compile(r"[\[(]\s*required\s*[\])]|\brequired\b\.?$", re.IGNORECASE)
_USAGE = re.compile(r"^\s*usage\s*:?\s*(.*)$", re.IGNORECASE)


def clean(text: str) -> str:
    text = _ANSI.sub("", text or "")
    text = re.sub(r".\x08", "", text)  # man-page overstrike
    return text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(8)


def _normalize_arg(arg: str) -> str:
    arg = arg.strip().lstrip("=").strip()
    return arg


def _parse_spec(spec: str) -> dict:
    names, arg = [], ""
    for m in _FLAG_TOKEN.finditer(spec):
        flag, a = m.group(1), _normalize_arg(m.group(2))
        flag = flag.rstrip(",.:")
        if flag in ("-", "--"):
            continue
        names.append(flag)
        if a and not arg:
            arg = a
    longs = [n for n in names if n.startswith("--")]
    shorts = [n for n in names if not n.startswith("--")]
    if longs:
        name, short = longs[0], (shorts[0] if shorts else "")
        aliases = longs[1:] + shorts[1:]
    else:
        # single-dash only: -h, or Go/nmap-style long single-dash flags (-iL, -list)
        two = [n for n in shorts if len(n) == 2]
        multi = sorted((n for n in shorts if len(n) > 2), key=len, reverse=True)
        name = multi[0] if multi else (two[0] if two else "")
        short = two[0] if two and two[0] != name else ""
        aliases = [n for n in shorts if n not in (name, short)]
    return {"name": name, "short": short if short != name else "", "aliases": aliases, "arg": arg}


def _is_commands_header(h: str) -> bool:
    return bool(re.search(r"\b(sub)?commands?\b", h, re.IGNORECASE)) and not re.search(r"option|flag", h, re.IGNORECASE)


def parse_help(text: str, tool: str = "") -> dict:
    """Return ``{"usage": str, "flags": [...], "subcommands": [...], "sections": [...]}``."""
    lines = clean(text).split("\n")
    usage, flags, subcommands, sections = "", [], [], []
    seen, section, cur, cur_indent = set(), "", None, 0
    in_usage = False

    def finish():
        nonlocal cur
        if cur is not None:
            desc = re.sub(r"\s+", " ", cur["description"]).strip()
            d = _DEFAULT.search(desc)
            cur["default"] = d.group(1).strip().strip("'\"") if d else ""
            cur["required"] = bool(_REQUIRED.search(desc))
            if desc.startswith("|"):  # hashcat-style table: | ARG | description | example
                cells = [c.strip() for c in desc.strip("|").split("|")]
                if len(cells) >= 2:
                    if cells[0] and not cur["arg"]:
                        cur["arg"] = cells[0]
                    desc = cells[1]
                    if len(cells) > 2 and cells[2]:
                        cur["table_example"] = cells[2]
            cur["description"] = desc
            flags.append(cur)
        cur = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if cur is not None and cur["description"]:
                finish()
            in_usage = False
            continue
        um = _USAGE.match(line)
        if um and not usage and not line.startswith(" " * 6):
            usage = um.group(1).strip()
            in_usage = not usage
            continue
        if in_usage:
            if line.startswith(" "):
                usage = stripped
            in_usage = False
            continue
        hm = _HEADER.match(line)
        if hm and not line.startswith("  ") and not stripped.startswith("-"):
            finish()
            section = hm.group("h").strip()
            sections.append(section)
            continue
        sm = _SPEC.match(line)
        if sm and stripped.startswith("-"):
            spec = _parse_spec(sm.group("spec"))
            if spec["name"]:
                finish()
                cur_indent = len(sm.group("indent"))
                key = spec["name"]
                if key in seen:
                    cur = None
                    continue
                seen.add(key)
                cur = {**spec, "description": sm.group("desc").strip(), "section": section}
                continue
        if section and _is_commands_header(section):
            cm = _CMD_LINE.match(line)
            if cm:
                finish()
                name = cm.group("name")
                if name not in {s["name"] for s in subcommands}:
                    subcommands.append({"name": name, "description": cm.group("desc").strip()})
                continue
        if cur is not None:
            indent = len(line) - len(line.lstrip())
            if indent > cur_indent or not cur["description"]:
                cur["description"] += " " + stripped
                continue
            finish()
    finish()
    for f in flags:
        table_example = f.pop("table_example", "")
        f["example"] = f"{tool} {table_example}" if tool and table_example else example_for(tool, f)
    return {"usage": usage, "flags": flags, "subcommands": subcommands, "sections": sections}


def example_for(tool: str, flag: dict, sub: str = "") -> str:
    """Template example built only from parsed pieces (marked as synthesized by callers)."""
    if not tool:
        return ""
    parts = [tool] + ([sub] if sub else []) + [flag["name"]]
    if flag.get("arg"):
        a = flag["arg"].strip("[]{}")
        a = a if a.startswith("<") else f"<{a.lower()}>"
        parts.append(a)
    return " ".join(parts)


FLAG_IN_CMD = re.compile(r"(?<![\w/.:=-])(--?[A-Za-z][\w\-]*)")


def flags_in_command(cmd: str) -> list[str]:
    """Flags used in a command line (``--out=x`` → ``--out``)."""
    return [m.group(1) for m in FLAG_IN_CMD.finditer(cmd)]


def known_flag_names(parsed_flags: list[dict]) -> set[str]:
    names = set()
    for f in parsed_flags:
        for n in [f.get("name"), f.get("short"), *(f.get("aliases") or [])]:
            if n:
                names.add(n.split("[")[0])
                if "[no-]" in n:
                    names.add(n.replace("[no-]", ""))
                    names.add(n.replace("[no-]", "no-"))
    return names
