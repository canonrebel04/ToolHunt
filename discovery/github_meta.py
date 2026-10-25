"""Batch GitHub repository metadata via GraphQL (stars, archived, last push, license, language)."""
from __future__ import annotations

import json
import re

from .http import fetch, github_token

GRAPHQL_URL = "https://api.github.com/graphql"
_REPO = re.compile(r"^https://github\.com/([^/]+)/([^/]+)$")
_FIELDS = "stargazerCount isArchived isFork pushedAt description licenseInfo { spdxId } primaryLanguage { name }"


def split_repo(url: str):
    m = _REPO.match(url or "")
    return (m.group(1), m.group(2)) if m else None


def build_query(repos: list[tuple[str, str]]) -> str:
    parts = []
    for i, (owner, name) in enumerate(repos):
        parts.append(f"r{i}: repository(owner: {json.dumps(owner)}, name: {json.dumps(name)}) {{ {_FIELDS} }}")
    return "query { " + " ".join(parts) + " }"


def parse_response(repos: list[tuple[str, str]], payload: dict) -> dict[str, dict]:
    out = {}
    data = payload.get("data") or {}
    for i, (owner, name) in enumerate(repos):
        r = data.get(f"r{i}")
        if not r:
            continue
        lic = ((r.get("licenseInfo") or {}).get("spdxId") or "").replace("NOASSERTION", "")
        out[f"https://github.com/{owner}/{name}".lower()] = {
            "stars": r.get("stargazerCount"),
            "archived": bool(r.get("isArchived")),
            "fork": bool(r.get("isFork")),
            "last_commit": (r.get("pushedAt") or "")[:10],
            "license": lic,
            "language": (r.get("primaryLanguage") or {}).get("name") or "",
            "repo_description": r.get("description") or "",
        }
    return out


def fetch_repo_meta(urls, batch: int = 80, log=print) -> dict[str, dict]:
    """Return ``{canonical_repo_url: meta}``. Requires GITHUB_TOKEN; returns {} without one."""
    tok = github_token()
    if not tok:
        log("github_meta: no GITHUB_TOKEN, skipping enrichment")
        return {}
    repos = sorted({r for r in (split_repo(u) for u in urls) if r})
    out: dict[str, dict] = {}
    for start in range(0, len(repos), batch):
        chunk = repos[start:start + batch]
        body = json.dumps({"query": build_query(chunk)}).encode()
        try:
            payload = json.loads(fetch(GRAPHQL_URL, data=body, headers={
                "Authorization": f"Bearer {tok}", "Content-Type": "application/json"}, timeout=90))
        except Exception as e:  # noqa: BLE001 - one bad batch must not kill the run
            log(f"github_meta: batch {start // batch} failed: {e}")
            continue
        out.update(parse_response(chunk, payload))
    return out
