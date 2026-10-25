"""Tiny stdlib HTTP helpers (no extra dependencies)."""
import json
import os
import time
import urllib.error
import urllib.request

USER_AGENT = "ToolHunt-discovery/1.0 (+https://github.com/canonrebel04/ToolHunt)"


def fetch(url: str, *, headers: dict | None = None, data: bytes | None = None,
          timeout: int = 60, retries: int = 3) -> bytes:
    hdrs = {"User-Agent": USER_AGENT, **(headers or {})}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=hdrs, data=data)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt * 2)
    raise RuntimeError("unreachable")


def fetch_text(url: str, **kw) -> str:
    return fetch(url, **kw).decode("utf-8", "replace")


def fetch_json(url: str, **kw):
    return json.loads(fetch(url, **kw))


def github_token() -> str:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""


def github_headers() -> dict:
    tok = github_token()
    h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h
