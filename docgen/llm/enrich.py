"""Merge LLM enrichment into a Tier-1 doc with strict validation."""
from __future__ import annotations

import json
import re
from copy import deepcopy
from typing import Any

from docgen.helpparse import flags_in_command, known_flag_names
from docgen.llm.providers import LLMConfig, chat_completion

GENERATOR = "tier2-llm"
_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

SYSTEM_PROMPT = """You enrich CLI tool documentation. Reply with a single JSON object only.
Rules:
- Never invent flag names, short forms, or arguments. Only rewrite descriptions/examples for flags listed in the input.
- summary: 2–4 plain sentences on what the tool does and when to use it.
- highlights: up to 8 short bullets (feature chips).
- flags: array of {name, description, example} — name must match an input flag exactly; example must use only known flags.
- examples: 3–8 {cmd, explanation} recipes using only known flags/subcommands.
- see_also: up to 8 related tool ids/names.
- Do not include install methods.
"""


def _extract_json(text: str) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("empty LLM response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = _JSON_FENCE.search(text)
        if m:
            return json.loads(m.group(1))
        # last resort: first { ... } span
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def _validate_examples(examples: list[dict], known: set[str]) -> list[dict]:
    if not isinstance(examples, list):
        return []
    kept = []
    for ex in examples:
        if not isinstance(ex, dict):
            continue
        cmd = (ex.get("cmd") or "").strip()
        if not cmd:
            continue
        used = flags_in_command(cmd)
        if known and used and not all(u in known for u in used):
            continue
        kept.append({
            "cmd": cmd,
            "explanation": str(ex.get("explanation") or "").strip(),
            "source": ex.get("source") or "llm",
            "verified": True,
        })
    return kept


def merge_enrichment(base: dict, llm: dict, *, provider: str = "", model: str = "") -> dict:
    """Apply LLM fields onto a Tier-1 doc. Flag identities stay locked to ``base``."""
    out = deepcopy(base)
    known = known_flag_names(out.get("flags") or [])
    by_name = {}
    for f in out.get("flags") or []:
        if f.get("name"):
            by_name[f["name"]] = f
        if f.get("short"):
            by_name[f["short"]] = f

    summary = (llm.get("summary") or "").strip()
    if summary:
        out["summary"] = summary

    highlights = llm.get("highlights")
    if isinstance(highlights, list):
        out["highlights"] = [str(h).strip() for h in highlights if str(h).strip()][:8]

    # Update flag descriptions/examples only when name matches
    for item in llm.get("flags") or []:
        if not isinstance(item, dict):
            continue
        name = (item.get("name") or "").strip()
        target = by_name.get(name)
        if target is None:
            continue
        desc = (item.get("description") or "").strip()
        if desc:
            target["description"] = desc
        example = (item.get("example") or "").strip()
        if example:
            used = flags_in_command(example)
            if not known or not used or all(u in known for u in used):
                target["example"] = example

    llm_examples = _validate_examples(llm.get("examples") or [], known)
    if llm_examples:
        # Prefer LLM recipes but keep any pre-validated tldr/showcase ones that remain unique
        existing_cmds = {e.get("cmd") for e in llm_examples}
        preserved = [e for e in (out.get("examples") or []) if e.get("cmd") not in existing_cmds]
        out["examples"] = llm_examples + preserved[:5]

    see = llm.get("see_also")
    if isinstance(see, list):
        out["see_also"] = [str(s).strip() for s in see if str(s).strip()][:8]

    tag = f"llm:{provider or 'unknown'}:{model or 'unknown'}"
    sources = list(out.get("sources") or [])
    if tag not in sources:
        sources.append(tag)
    out["sources"] = sources

    verified = dict(out.get("verified") or {})
    verified["llm_enriched"] = True
    verified["examples_checked"] = True
    out["verified"] = verified
    out["generator"] = GENERATOR
    out["model"] = model or ""
    return out


def _user_payload(doc: dict, *, help_text: str = "", readme: str = "") -> str:
    slim_flags = [
        {
            "name": f.get("name"),
            "short": f.get("short"),
            "arg": f.get("arg"),
            "description": f.get("description"),
            "section": f.get("section", ""),
        }
        for f in (doc.get("flags") or [])[:80]
    ]
    payload: dict[str, Any] = {
        "id": doc.get("id"),
        "name": doc.get("name"),
        "summary": doc.get("summary"),
        "usage": doc.get("usage"),
        "subcommands": doc.get("subcommands") or [],
        "flags": slim_flags,
        "examples": (doc.get("examples") or [])[:6],
        "install": doc.get("install") or [],
    }
    if help_text:
        payload["help_excerpt"] = help_text[:6000]
    if readme:
        payload["readme_excerpt"] = readme[:4000]
    return json.dumps(payload, ensure_ascii=False)


def enrich_doc(
    doc: dict,
    *,
    help_text: str = "",
    readme: str = "",
    config: LLMConfig | None = None,
    chat=None,
) -> dict:
    """Call the configured LLM and merge a validated enrichment into ``doc``."""
    cfg = config or LLMConfig.from_env()
    chat_fn = chat or chat_completion
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _user_payload(doc, help_text=help_text, readme=readme)},
    ]
    raw = chat_fn(messages, config=cfg)
    parsed = _extract_json(raw)
    if not isinstance(parsed, dict):
        raise TypeError("LLM JSON root must be an object")
    return merge_enrichment(doc, parsed, provider=cfg.provider, model=cfg.model)
