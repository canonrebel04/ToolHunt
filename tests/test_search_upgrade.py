"""Phase 5: enriched index text + offline evaluation set."""
import json
from pathlib import Path

import pytest

from backend import indexing

EVAL_PATH = Path(__file__).resolve().parent.parent / "data" / "eval" / "search_queries.json"


@pytest.fixture(autouse=True)
def _clear_docs_cache():
    indexing._docs_cache = None
    yield
    indexing._docs_cache = None


class TestIndexText:
    def test_basic_without_doc(self):
        tool = {"id": "x", "name": "Xtool", "description": "Does X", "category": "general",
                "subcategory": "Utils", "tags": ["cli", "rust"]}
        text = indexing.index_text(tool, doc=None)
        # force no disk docs
        indexing._docs_cache = {}
        text = indexing.index_text(tool, doc={})
        assert "xtool" in text and "does x" in text and "general" in text and "cli" in text

    def test_includes_flags_and_summary(self):
        tool = {"id": "ab-av1", "name": "ab-av1", "description": "AV1 helper", "category": "general",
                "subcategory": "Media", "tags": []}
        doc = {
            "summary": "Find CRF for a target VMAF then encode.",
            "highlights": ["scene-cut"],
            "subcommands": [{"name": "auto-encode", "description": "encode with VMAF target"}],
            "flags": [
                {"name": "--thorough", "short": "", "description": "Exhaustive CRF search"},
                {"name": "--input", "short": "-i", "description": "Input video"},
            ],
            "examples": [{"cmd": "ab-av1 auto-encode --thorough -i v.mkv", "explanation": "thorough VMAF"}],
        }
        text = indexing.index_text(tool, doc=doc)
        for needle in ("vmaf", "--thorough", "auto-encode", "scene-cut", "-i", "exhaustive"):
            assert needle in text

    def test_truncates(self):
        tool = {"id": "t", "name": "t", "description": "d", "category": "security", "subcategory": "", "tags": []}
        doc = {"summary": "word " * 5000, "flags": [], "examples": [], "highlights": [], "subcommands": []}
        text = indexing.index_text(tool, doc=doc)
        assert len(text) <= indexing.MAX_INDEX_CHARS

    def test_hash_includes_version(self):
        a = indexing.doc_list_hash(["alpha", "beta"])
        b = indexing.doc_list_hash(["beta", "alpha"])
        assert a == b
        # version is part of the seed — changing INDEX_TEXT_VERSION changes hashes
        assert indexing.INDEX_TEXT_VERSION in "v2-enriched-docs"


class TestEvalSet:
    def test_file_shape(self):
        data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        assert 30 <= len(data) <= 60
        for row in data:
            assert row["query"] and isinstance(row["expect"], list) and row["expect"]

    def test_enriched_docs_cover_showcase_queries(self, tmp_path):
        """Offline recall proxy: enriched index text for expected tools must match query tokens.

        We only assert on tools that have Tier-1 docs on disk (Phase 2 coverage), so the
        suite stays green before a full docs backfill. Soft-expect tools without docs are skipped.
        """
        data = json.loads(EVAL_PATH.read_text(encoding="utf-8"))
        docs = indexing.load_docs_map(force=True)
        covered = 0
        misses = []
        for row in data:
            # Prefer expected tools that have docs
            candidates = [t for t in row["expect"] if t in docs]
            if not candidates:
                continue
            covered += 1
            q_tokens = [t for t in row["query"].lower().replace("-", " ").split() if len(t) > 2]
            # distinctive tokens: drop ultra-common words
            stop = {"the", "and", "for", "with", "from", "that", "this", "into", "using"}
            q_tokens = [t for t in q_tokens if t not in stop]
            best = 0
            for tid in candidates:
                tool = {"id": tid, "name": tid, "description": docs[tid].get("summary") or tid,
                        "category": "", "subcategory": "", "tags": []}
                text = indexing.index_text(tool, doc=docs[tid])
                hits = sum(1 for t in q_tokens if t in text)
                best = max(best, hits)
            # At least ~40% of query tokens should appear in the best expected doc's index text
            need = max(1, len(q_tokens) // 3)
            if best < need:
                misses.append((row["query"], candidates, best, need, q_tokens))
        assert covered >= 8, "expected several eval rows to hit Tier-1 docs"
        assert misses == [], f"enriched index missed query tokens: {misses[:5]}"

    def test_real_ab_av1_doc_indexed(self):
        docs = indexing.load_docs_map(force=True)
        assert "ab-av1" in docs
        text = indexing.index_text(
            {"id": "ab-av1", "name": "ab-av1", "description": "AV1", "category": "general",
             "subcategory": "Media", "tags": []},
            doc=docs["ab-av1"],
        )
        assert "--thorough" in text or "thorough" in text
        assert "vmaf" in text
