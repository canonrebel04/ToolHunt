"""Quality gates for *new* tools (existing tools are always merged/refreshed)."""
from __future__ import annotations

import math
from datetime import date

MIN_DESC = 10
CURATED = ("blackarch", "kali", "homebrew")  # hand-maintained package lists


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


def reject_reason(cand: dict, meta: dict | None, today: date | None = None) -> str | None:
    """Return why a new candidate should be skipped, or None to accept it."""
    if len((cand.get("description") or "").strip()) < MIN_DESC:
        return "short-description"
    srcs = cand.get("sources") or []
    curated = any(s in CURATED for s in srcs)
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
    return None
