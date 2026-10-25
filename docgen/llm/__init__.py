"""Pluggable LLM clients for Tier-2 doc enrichment."""

from .enrich import enrich_doc, merge_enrichment
from .providers import LLMConfig, chat_completion, list_providers

__all__ = [
    "LLMConfig",
    "chat_completion",
    "enrich_doc",
    "list_providers",
    "merge_enrichment",
]
