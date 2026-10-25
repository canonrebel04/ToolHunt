"""tldr-pages (CC BY 4.0) examples: https://github.com/tldr-pages/tldr"""
from __future__ import annotations

import io
import re
import zipfile

TLDR_ZIP_URL = "https://github.com/tldr-pages/tldr/releases/latest/download/tldr.zip"
PLATFORMS = ("common", "linux", "osx")
_OPTION = re.compile(r"\{\{\[([^\]|]+)\|([^\]|]+)\]\}\}")  # {{[-F|--fixed-strings]}}
_PLACEHOLDER = re.compile(r"\{\{(.+?)\}\}")


def render(cmd: str) -> str:
    """``rg {{[-F|--fixed-strings]}} {{pattern}}`` → ``rg --fixed-strings <pattern>``."""
    cmd = _OPTION.sub(lambda m: m.group(2).strip(), cmd)
    return _PLACEHOLDER.sub(lambda m: f"<{m.group(1).strip()}>", cmd)


def parse_page(md: str) -> dict:
    title, desc, more, examples, pending = "", [], "", [], None
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("# "):
            title = s[2:].strip()
        elif s.startswith("> "):
            t = s[2:].strip()
            m = re.match(r"More information:\s*<([^>]+)>", t)
            if m:
                more = m.group(1)
            elif not t.startswith(("See also", "Note:", "This command is an alias")):
                desc.append(t)
        elif s.startswith("- "):
            pending = s[2:].rstrip(":").strip()
        elif s.startswith("`") and s.endswith("`") and pending is not None:
            examples.append({"cmd": render(s[1:-1]), "explanation": pending})
            pending = None
    return {"name": title, "description": " ".join(desc), "more_info": more, "examples": examples}


def load_pages(data: bytes) -> dict[str, dict]:
    """``{page_name: parsed}`` from the tldr release zip (English pages; common wins)."""
    pages: dict[str, dict] = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for plat in reversed(PLATFORMS):  # common last so it overrides
            prefix = f"pages/{plat}/"
            for n in z.namelist():
                if n.startswith(prefix) and n.endswith(".md"):
                    page = parse_page(z.read(n).decode("utf-8", "replace"))
                    page["platform"] = plat
                    page["path"] = n
                    pages[n[len(prefix):-3]] = page
    return pages
