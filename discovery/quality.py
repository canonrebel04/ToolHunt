"""Quality gates for *new* tools (existing tools are always merged/refreshed).

GitHub-topic-only finds must be confirmed by a package/curated source
(Homebrew, Kali, BlackArch, cli-apps / awesome-cli-apps, tldr, …) **or**
pass strong CLI-tool heuristics. Libraries, frameworks, awesome/notes lists,
large web platforms, and generic names are rejected.
"""
from __future__ import annotations

import math
import re
from datetime import date

MIN_DESC = 10
# Trusted enough to skip star/staleness gates (and confirm github finds).
CURATED = ("blackarch", "kali", "homebrew")
# Package / curated lists that confirm a GitHub-topic find.
PACKAGE_SOURCES = ("blackarch", "kali", "homebrew", "cli-apps", "tldr")

# Exact name/id denylist (libraries, frameworks, lists, platforms, generics).
BLOCKED_NAMES = frozenset({
    # libraries / frameworks
    "tqdm", "chalk", "typer", "cobra", "bubbletea", "ratatui", "textual",
    "textual-web", "click", "rich", "colorama", "blessed", "prompt-toolkit",
    "inquirer", "commander", "yargs", "meow", "ora", "ink",
    # awesome / reading / notes lists
    "modern-unix", "oscprepo", "hackingthe.cloud", "infosec_reference",
    "payloadsallthethings", "awesome-cli-apps", "awesome-shell", "awesome-hacking",
    "osint-framework", "ethical-hacking-labs", "black-hat-rust", "mastg",
    "allaboutbugbounty", "api-s-for-osint", "api-securityempire",
    "31-days-of-api-security-tips", "a-red-teamer-diaries", "aboutsecurity",
    "adversary_emulation_library", "anthropic-cybersecurity-skills",
    "redteam-tools", "web-fuzzing-box", "fbi-tools",
    # large web apps / platforms
    "n8n", "jeecgboot", "openhands", "worldmonitor", "gpt4free",
    # generic / too broad
    "terminal", "console", "content", "cli", "tool", "tools", "hack", "hacking",
    "security", "pentest", "pentesting", "framework", "library",
    # distros / meta repos mistaken for tools
    "blackarch", "kali-linux", "parrotlinux",
})

GENERIC_NAMES = frozenset({
    "terminal", "console", "content", "cli", "tool", "tools", "app", "apps",
    "util", "utils", "utility", "utilities", "bin", "cmd", "command",
})

_LISTY_NAME = re.compile(
    r"(^awesome[\w-]*|cheat-?sheets?|interview|roadmap|resources?$|-lists?$|"
    r"write-?ups?|notes$|course|diaries|tips$|reference$|payloads|"
    r"^osint-framework$|labs?$|skills$|curriculum|handbook|book$)",
    re.IGNORECASE,
)
_LISTY_DESC = re.compile(
    r"\b(curated (list|collection)|collection of (resources|links|tools|scripts)|"
    r"awesome list|cheat ?sheets?|roadmap|interview questions|tutorials?|"
    r"write-?ups?|books?|notes for|learning (path|resource)|skill(?:s)? (bundle|pack)|"
    r"reference (that|for)|payloads? (list|collection)|dictionary of)\b",
    re.IGNORECASE,
)
_LIBRARY_RE = re.compile(
    r"\b("
    r"librar(y|ies)|npm package|python package|pypi|crate for|go module|"
    r"bindings for|SDK for|framework for|UI framework|TUI (framework|library|crate)|"
    r"application framework|progress bar for|string styl(?:ing|e)|"
    r"build great CLIs|CLI framework|command(?:-|\s)?line framework|"
    r"terminal user interfaces?|cooking up terminal|"
    r"React for (the )?terminal|component library"
    r")\b",
    re.IGNORECASE,
)
_PLATFORM_RE = re.compile(
    r"\b("
    r"workflow automation platform|low-?code|no-?code platform|"
    r"enterprise (platform|ERP)|web (application )?framework|"
    r"AI-?Driven Development|agentic IDE|coding agent harness|"
    r"desktop app with one command|"  # pake-style website wrappers
    r"self-hosted AI Agents system"
    r")\b",
    re.IGNORECASE,
)
# Positive CLI / installable-tool signals (stand in for binary + README usage).
_CLI_POSITIVE = re.compile(
    r"("
    r"\bcommand[ -]line\b|\bcli (tool|utility|app|application|client|scanner|fuzzer)\b|"
    r"\bterminal (tool|utility|app|client|multiplexer|emulator|file manager)\b|"
    r"\bfrom the (command line|terminal)\b|"
    r"\b(install|run|usage):\s*`|"
    r"`[a-z][\w.-]*\s+--|"
    r"\bCLI\b.*\b(tool|utility|scanner|client)\b|"
    r"\b(written|implemented) in (go|rust|c\+\+|c)\b.*\b(cli|command)"
    r")",
    re.IGNORECASE,
)
_SECURITY_TOOL_POS = re.compile(
    r"\b("
    r"scanner|fuzzer|exploiter?|sniffer|bruteforce|brute[- ]force|"
    r"enumeration|recon(naissance)?(\s+(framework|tool|engine|suite))?|forensics?|"
    r"disassembl|memory (forensics?|analysis|extraction)|volatile memory|"
    r"password crack|hash crack|vulnerability (scanner|assessment)|"
    r"pentest(ing)?(\s+tool)?|security (scanner|tool|analyzer|auditor|orchestration)|"
    r"packet (capture|analyzer)|firmware (analyzer|security)|"
    r"osint tool|subdomain|wordlist|payload generator|"
    r"orchestration engine for security|automated recon|"
    r"AI pentester|penetration testing tool"
    r")\b",
    re.IGNORECASE,
)


def _norm_name(cand: dict) -> str:
    return (cand.get("id") or cand.get("name") or "").strip().lower()


def _sources(cand: dict) -> list[str]:
    raw = cand.get("sources") or []
    if isinstance(raw, str):
        try:
            import json
            raw = json.loads(raw)
        except ValueError:
            raw = [raw] if raw else []
    return [str(s) for s in raw]


def is_package_confirmed(sources: list[str]) -> bool:
    for s in sources:
        base = s.split(":", 1)[0]
        if base in PACKAGE_SOURCES or s.startswith("tldr"):
            return True
    return False


def is_github_topic_only(sources: list[str]) -> bool:
    return bool(sources) and all(s.startswith("github:") for s in sources)


def looks_like_cli_tool(cand: dict, meta: dict | None = None) -> bool:
    """Strong heuristic: installable CLI / security tool, not a library or list.

    Optional ``meta`` may carry ``has_bin`` / ``readme_cli`` from enrichment;
    without those we rely on name + description (and language).
    """
    name = _norm_name(cand)
    if not name or name in BLOCKED_NAMES or name in GENERIC_NAMES:
        return False
    if _LISTY_NAME.search(name):
        return False
    # Well-known CLI/security tool name prefixes with thin GitHub descriptions.
    if name.startswith(("volatility", "wireshark", "nmap", "sqlmap", "hashcat", "john")):
        return True
    desc = cand.get("description") or (meta or {}).get("repo_description") or ""
    blob = f"{name} {desc}"
    cli_pos = bool(_CLI_POSITIVE.search(desc) or (
        cand.get("category") == "security" and _SECURITY_TOOL_POS.search(desc)
    ))
    if _LISTY_DESC.search(desc):
        return False
    if (_LIBRARY_RE.search(blob) or _PLATFORM_RE.search(blob)) and not cli_pos:
        return False
    if (meta or {}).get("has_bin") or (meta or {}).get("readme_cli"):
        return True
    if cli_pos:
        return True
    # Language alone is weak; only help when description already says "tool"/"utility"
    lang = ((meta or {}).get("language") or cand.get("language") or "").lower()
    return bool(
        lang in ("go", "rust", "shell", "c", "c++")
        and re.search(r"\b(tool|utility|scanner|client|binary)\b", desc, re.IGNORECASE)
    )


def reject_reason(cand: dict, meta: dict | None, today: date | None = None) -> str | None:
    """Return why a new candidate should be skipped, or None to accept it."""
    desc = (cand.get("description") or "").strip()
    if len(desc) < MIN_DESC:
        return "short-description"

    name = _norm_name(cand)
    if name in BLOCKED_NAMES or name in GENERIC_NAMES:
        return "blocked-name"
    if _LISTY_NAME.search(name) or _LISTY_DESC.search(desc):
        return "list-or-notes"
    blob = f"{name} {desc}"
    # Soft library/platform gate: real scanners/CLIs often say "framework for web apps".
    if _LIBRARY_RE.search(blob) and not (
        _CLI_POSITIVE.search(desc) or _SECURITY_TOOL_POS.search(desc)
    ):
        return "library-or-framework"
    if _PLATFORM_RE.search(blob) and not (
        _CLI_POSITIVE.search(desc) or _SECURITY_TOOL_POS.search(desc)
    ):
        return "web-platform"

    srcs = _sources(cand)
    curated = any(s in CURATED for s in srcs)
    package = is_package_confirmed(srcs)

    if meta:
        if meta.get("fork") and not curated:
            return "fork"
        stars = meta.get("stars") or 0
        if meta.get("archived") and not curated:
            return "archived"
        if not curated:
            min_stars = 100 if cand.get("category") == "general" else 30
            if stars < min_stars:
                return "low-stars"
            if stars < 500 and _years_since(meta.get("last_commit") or "", today) > 3:
                return "stale"

    # GitHub-topic-only must be package-confirmed or look like a real CLI tool.
    if is_github_topic_only(srcs) and not package and not looks_like_cli_tool(cand, meta):
        return "github-unconfirmed"

    return None


def should_purge_existing(tool: dict) -> str | None:
    """If an existing DB row should be removed under the tightened filter, return why.

    Package/curated-confirmed tools are kept (except exact ``BLOCKED_NAMES`` /
    ``GENERIC_NAMES``). GitHub-topic-only rows are re-checked with
    ``reject_reason``. Pre-discovery legacy rows are only dropped on exact
    blocked/generic names or an obvious list-style *name* — never on soft
    library/desc heuristics (avoids deleting Metasploit et al.).
    """
    srcs = _sources(tool)
    name = _norm_name(tool)
    if name in BLOCKED_NAMES or name in GENERIC_NAMES:
        return "blocked-name"
    if is_package_confirmed(srcs):
        return None
    if is_github_topic_only(srcs):
        meta = {
            "stars": tool.get("stars") or 0,
            "archived": bool(tool.get("archived")),
            "fork": False,
            "last_commit": tool.get("last_commit") or "",
            "language": tool.get("language") or "",
            "repo_description": tool.get("description") or "",
        }
        return reject_reason(
            {
                "name": tool.get("name") or name,
                "id": tool.get("id") or name,
                "description": tool.get("description") or "",
                "category": tool.get("category") or "security",
                "sources": srcs,
                "language": tool.get("language") or "",
            },
            meta,
        )
    # Legacy / unknown sources: only obvious list repos by name.
    if _LISTY_NAME.search(name):
        return "list-or-notes"
    return None


def _years_since(day: str, today: date | None = None) -> float:
    try:
        d = date.fromisoformat(day[:10])
    except (TypeError, ValueError):
        return 0.0
    return ((today or date.today()) - d).days / 365.25


def score(meta: dict | None, sources: list[str]) -> float:
    stars = (meta or {}).get("stars") or 0
    s = min(1.0, math.log10(stars + 1) / 5) * 0.7 + min(len(sources), 3) / 3 * 0.3
    return round(s, 3)

# Public aliases for source parsers
LISTY_NAME = _LISTY_NAME
LISTY_DESC = _LISTY_DESC
LIBRARY_RE = _LIBRARY_RE
PLATFORM_RE = _PLATFORM_RE
