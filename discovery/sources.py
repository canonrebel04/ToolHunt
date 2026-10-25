"""Discovery sources. Each ``parse_*`` is pure (text in, candidates out) so it can be
unit-tested offline; each ``collect_*`` fetches the live data and calls its parser.

A candidate is a dict accepted by :func:`backend.db.upsert_tool` plus ``aliases``.
"""
from __future__ import annotations

import csv
import io
import json
import re
import tarfile
import time

from .http import fetch, fetch_json, fetch_text, github_headers

BLACKARCH_URL = "https://raw.githubusercontent.com/BlackArch/blackarch-site/master/data/tools"
KALI_ARCHIVE_URL = "https://gitlab.com/kalilinux/documentation/kali-tools/-/archive/main/kali-tools-main.tar.gz"
CLI_APPS_URL = "https://raw.githubusercontent.com/toolleeo/cli-apps/master/data/apps.csv"
BREW_ANALYTICS_URL = "https://formulae.brew.sh/api/analytics/install-on-request/90d.json"
BREW_FORMULA_URL = "https://formulae.brew.sh/api/formula.json"
GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

SECURITY_TOPICS = ["pentesting", "penetration-testing", "red-team", "osint", "bug-bounty",
                   "security-tools", "reconnaissance", "fuzzing", "forensics", "reverse-engineering"]
GENERAL_TOPICS = ["cli", "command-line-tool", "terminal"]


def label(slug: str) -> str:
    """'information-gathering' -> 'Information Gathering'."""
    return " ".join(w.capitalize() for w in re.split(r"[-_\s]+", slug.strip()) if w)


def _clean(text: str, limit: int = 400) -> str:
    text = re.sub(r"\s+", " ", (text or "").replace("`", "")).strip()
    return text if len(text) <= limit else text[: limit - 1].rsplit(" ", 1)[0] + "…"


# ── BlackArch ─────────────────────────────────────────────────────────
_BA_SKIP_GROUPS = {"blackarch"}


def parse_blackarch(text: str):
    """``name|version|description|groups|url`` lines."""
    for line in text.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5 or not parts[0]:
            continue
        name, _ver, desc, groups, url = parts[:5]
        grp = [g.removeprefix("blackarch-") for g in groups.split() if g not in _BA_SKIP_GROUPS]
        yield {
            "name": name, "description": _clean(desc), "url": url, "category": "security",
            "subcategory": label(grp[0]) if grp else "", "tags": grp, "sources": ["blackarch"],
        }


def collect_blackarch():
    return list(parse_blackarch(fetch_text(BLACKARCH_URL)))


# ── Kali (kali-tools documentation repo: one index.md per tool) ──────
_FRONT_KEY = re.compile(r"^([A-Za-z]+):\s?(.*)$")
_KALI_SKIP_META = {"kali-tools-top10"}


def parse_kali_frontmatter(md: str) -> dict:
    """Return top-level frontmatter keys; ``PackagesInfo`` is the raw block text."""
    m = re.match(r"^---\s*\n(.*?)\n---", md, re.DOTALL)
    if not m:
        return {}
    out, key, block = {}, None, []
    for line in m.group(1).splitlines():
        km = _FRONT_KEY.match(line)
        if km and not line.startswith(" "):
            if key == "PackagesInfo":
                out[key] = "\n".join(block)
            key, val = km.group(1), km.group(2).strip()
            out[key] = val
            block = []
        elif key == "PackagesInfo":
            block.append(line.removeprefix(" "))
    if key == "PackagesInfo":
        out[key] = "\n".join(block)
    return out


_SECURITY_WORDS = re.compile(
    r"(exploit|pentest|penetration|vulnerab|attack|brute|sniff|spoof|crack|password|hash|recon|"
    r"enumerat|forensic|malware|post-exploitation|\bc2\b|red team|active directory|kerberos|ldap|smb|"
    r"fuzz|scanner|scanning|osint|phish|payload|privilege|backdoor|wireless|wifi|wi-fi|bluetooth|"
    r"rogue|mitm|man-in-the-middle|intercept|reverse engineer|disassembl|debugger|shellcode|"
    r"bloodhound|azure|wordlist|subdomain|steganograph|evil|hack|security|audit|tunnel|proxy|"
    r"\bdns\b|\bsnmp\b|\bssl\b|\btls\b|certificate|honeypot|ids\b|firewall|packet|traffic|"
    r"capture|memory image|keylog|credential|ntlm|relay|harvest|discovery|secret|intelligence|adversar|"
    r"command and control|coerce|authenticat|domain|spider|crawl|screenshot|\bdos\b|encrypt|bitlocker|"
    r"dpapi|enum|nmap|netcat|metasploit|\bgdb\b|volatility|breach|permutation|exposed|leak|radius)",
    re.IGNORECASE,
)


def _kali_description(info: str, title: str) -> str:
    sec = re.search(rf"^###\s+{re.escape(title)}\s*$(.*?)(?=^###\s|\Z)", info, re.MULTILINE | re.DOTALL)
    body = sec.group(1) if sec else info
    bm = re.search(r"^\s*\*\*(.+?)\*\*\s*$", body, re.MULTILINE)
    if bm and not bm.group(1).rstrip().endswith(":"):
        return bm.group(1)
    para = []
    for line in body.splitlines():
        t = line.strip()
        if t.startswith(("**", "{{", "#")):
            if para:
                break
            continue
        if not t:
            if para:
                break
            continue
        para.append(t)
    text = " ".join(para)
    first = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    return first.rstrip(".")


def parse_kali_tool(md: str) -> dict | None:
    fm = parse_kali_frontmatter(md)
    title = fm.get("Title", "").strip()
    if not title or fm.get("archived", "").strip('"').lower() == "true":
        return None
    desc = _clean(_kali_description(fm.get("PackagesInfo", ""), title))
    metas = fm.get("Metapackages", "").split()
    cats = [m.removeprefix("kali-tools-") for m in metas if m.startswith("kali-tools-") and m not in _KALI_SKIP_META]
    # Kali also ships plain utilities; without a kali-tools-* metapackage keep the
    # tool only if its description looks security-related.
    if not cats and not _SECURITY_WORDS.search(f"{title} {desc}"):
        return None  # plain utility (browser, editor, SDK…); general tools come from other sources
    homepage = fm.get("Homepage", "").strip()
    return {
        "name": title, "description": desc, "url": homepage,
        "repo_url": (fm.get("Repository") or "").strip() if "github.com" not in homepage else homepage,
        "category": "security",
        "subcategory": label(cats[0]) if cats else "", "tags": cats, "sources": ["kali"],
    }


def iter_kali_archive(data: bytes):
    """Yield (tool_dir, index.md text) from the kali-tools repo tarball."""
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        for member in tar:
            parts = member.name.split("/")
            if member.isfile() and len(parts) == 3 and parts[2] == "index.md":
                f = tar.extractfile(member)
                if f:
                    yield parts[1], f.read().decode("utf-8", "replace")


def collect_kali():
    out = []
    for _dir, md in iter_kali_archive(fetch(KALI_ARCHIVE_URL, timeout=180)):
        tool = parse_kali_tool(md)
        if tool:
            out.append(tool)
    return out


# ── toolleeo/cli-apps (general CLI apps, CSV) ────────────────────────
def parse_cli_apps(text: str):
    for row in csv.DictReader(io.StringIO(text)):
        name = (row.get("name") or "").strip()
        if not name:
            continue
        git = (row.get("git") or "").strip()
        home = (row.get("homepage") or "").strip()
        cat = (row.get("category") or "").strip()
        yield {
            "name": name, "description": _clean(row.get("description") or ""),
            "url": git or home, "repo_url": git, "category": "general",
            "subcategory": label(cat) if cat else "", "tags": [cat] if cat else [], "sources": ["cli-apps"],
        }


def collect_cli_apps():
    return list(parse_cli_apps(fetch_text(CLI_APPS_URL)))


# ── Homebrew (most-installed formulae that are CLI tools) ─────────────
_BREW_SKIP_NAME = re.compile(r"^(lib|python|node|openjdk|ruby|perl|php|llvm|gcc|openssl|ca-certificates|icu4c)|@|-(dev|headers)$")
_BREW_SKIP_EXACT = {"hello", "pkgconf", "pkg-config", "harfbuzz", "rust", "dotnet", "automake", "autoconf",
                    "libtool", "gettext", "glib", "cairo", "pango", "freetype", "fontconfig", "xz", "zstd",
                    "protobuf", "go", "lua", "deno", "bun", "erlang", "elixir", "swift", "kotlin", "scala"}
_BREW_SKIP_DESC = re.compile(r"\b(librar(y|ies)|bindings|sdk|framework for|headers|runtime|toolchain|"
                             r"compiler collection|font|programming language|interpreter for)\b", re.IGNORECASE)


def parse_homebrew(analytics: dict, formulae: list, top_n: int = 600):
    by_name = {f["name"]: f for f in formulae}
    kept = 0
    for item in analytics.get("items", []):
        f = by_name.get(item.get("formula"))
        if not f or f.get("deprecated") or f.get("disabled"):
            continue
        name, desc = f["name"], f.get("desc") or ""
        if name in _BREW_SKIP_EXACT or _BREW_SKIP_NAME.search(name) or _BREW_SKIP_DESC.search(desc):
            continue
        home = f.get("homepage") or ""
        stable = ((f.get("urls") or {}).get("stable") or {}).get("url") or ""
        yield {
            "name": name, "description": _clean(desc), "url": home, "repo_url": home if "github.com" in home else stable,
            "category": "general", "license": f.get("license") or "", "sources": ["homebrew"],
            "aliases": f.get("aliases") or [],
        }
        kept += 1
        if kept >= top_n:
            break


def collect_homebrew(top_n: int = 600):
    return list(parse_homebrew(fetch_json(BREW_ANALYTICS_URL), fetch_json(BREW_FORMULA_URL, timeout=180), top_n))


# ── GitHub topic search ───────────────────────────────────────────────
_LISTY = re.compile(r"(^awesome|cheat-?sheet|interview|roadmap|resources?$|-list$|writeups?|notes$|course)", re.IGNORECASE)
_LISTY_DESC = re.compile(r"\b(curated list|collection of (resources|links|tools)|awesome list|cheat ?sheet|"
                         r"roadmap|interview questions|tutorials?|write-?ups?|books?)\b", re.IGNORECASE)


def parse_github_search(items: list, category: str, topic: str):
    for r in items:
        name, desc = r.get("name") or "", r.get("description") or ""
        if r.get("fork") or r.get("archived") or not desc or _LISTY.search(name) or _LISTY_DESC.search(desc):
            continue
        yield {
            "name": name, "description": _clean(desc), "url": r.get("html_url") or "",
            "repo_url": r.get("html_url") or "", "category": category, "subcategory": label(topic),
            "tags": [t for t in (r.get("topics") or [])][:10], "sources": [f"github:{topic}"],
            "stars": r.get("stargazers_count"), "last_commit": (r.get("pushed_at") or "")[:10],
            "language": r.get("language") or "",
            "license": ((r.get("license") or {}).get("spdx_id") or "").replace("NOASSERTION", ""),
        }


def collect_github_topics(security_min_stars: int = 300, general_min_stars: int = 3000, pages: int = 2):
    import urllib.parse

    out = []
    plan = [(t, "security", security_min_stars) for t in SECURITY_TOPICS] + \
           [(t, "general", general_min_stars) for t in GENERAL_TOPICS]
    for topic, category, min_stars in plan:
        for page in range(1, pages + 1):
            q = f"topic:{topic} stars:>={min_stars} archived:false fork:false"
            url = f"{GITHUB_SEARCH_URL}?{urllib.parse.urlencode({'q': q, 'sort': 'stars', 'per_page': 100, 'page': page})}"
            items = fetch_json(url, headers=github_headers()).get("items", [])
            time.sleep(2.5)  # search API: 30 requests/minute
            out.extend(parse_github_search(items, category, topic))
            if len(items) < 100:
                break
    return out


COLLECTORS = {
    "blackarch": collect_blackarch,
    "kali": collect_kali,
    "cli-apps": collect_cli_apps,
    "homebrew": collect_homebrew,
    "github": collect_github_topics,
}


def dumps(c):  # debugging helper
    return json.dumps(c, ensure_ascii=False)
