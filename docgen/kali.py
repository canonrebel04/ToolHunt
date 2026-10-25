"""Pre-captured help output from the Kali tools documentation (one index.md per package)."""
from __future__ import annotations

import re

from discovery.sources import parse_kali_frontmatter

_FENCE = re.compile(r"^```[^\n]*\n(.*?)^```", re.MULTILINE | re.DOTALL)
_PROMPT = re.compile(r"^root@kali:~#\s*(.+)$", re.MULTILINE)
_INSTALL = re.compile(r"\*\*How to install:\*\*\s*`([^`]+)`")


def help_blocks(md: str) -> list[dict]:
    """Return ``[{binary, command, output}]`` for every ``root@kali:~# cmd`` block."""
    info = parse_kali_frontmatter(md).get("PackagesInfo", "")
    out = []
    for fence in _FENCE.finditer(info):
        body = fence.group(1)
        prompts = list(_PROMPT.finditer(body))
        for i, pm in enumerate(prompts):
            end = prompts[i + 1].start() if i + 1 < len(prompts) else len(body)
            cmd = pm.group(1).strip()
            output = body[pm.end():end].strip("\n")
            if not output.strip():
                continue
            binary = cmd.split()[0].rsplit("/", 1)[-1]
            out.append({"binary": binary, "command": cmd, "output": output})
    return out


def install_commands(md: str, preferred: str = "") -> list[str]:
    info = parse_kali_frontmatter(md).get("PackagesInfo", "")
    cmds = list(dict.fromkeys(m.group(1).strip() for m in _INSTALL.finditer(info)))
    if preferred:
        pref = preferred.lower()
        cmds.sort(key=lambda c: 0 if pref in c.lower() else 1)
    return cmds


def best_block(blocks: list[dict], name: str) -> dict | None:
    """The help block for the tool's own binary (``nmap`` page also documents ``ncat``)."""
    if not blocks:
        return None
    low = name.lower()
    for b in blocks:
        if b["binary"].lower() == low:
            return b
    for b in blocks:
        if b["binary"].lower().startswith(low) or low.startswith(b["binary"].lower()):
            return b
    return blocks[0]
