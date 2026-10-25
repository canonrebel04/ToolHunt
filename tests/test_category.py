"""Category filter, tool detail API, and hybrid-search filtering/staleness."""
import json
import sys
from types import SimpleNamespace

import pytest


def _search(client, **body):
    return client.post("/search", data=json.dumps(body), content_type="application/json")


class TestCategoryRoute:
    def test_default_is_all(self, client):
        cats = {r["category"] for r in _search(client, query="tool", limit=100).get_json()["results"]}
        assert cats == {"security", "general"}

    @pytest.mark.parametrize("category", ["security", "general"])
    def test_filter(self, client, category):
        res = _search(client, query="tool", category=category, limit=100).get_json()["results"]
        assert res and all(r["category"] == category for r in res)

    def test_invalid_category(self, client):
        r = _search(client, query="tool", category="games")
        assert r.status_code == 400

    def test_results_have_id_and_subcategory(self, client):
        for r in _search(client, query="tool").get_json()["results"]:
            assert r["id"] and "subcategory" in r

    def test_cache_key_includes_category(self, client):
        a = _search(client, query="cachetest", category="general", limit=100).get_json()
        b = _search(client, query="cachetest", category="security", limit=100).get_json()
        assert a["total"] != b["total"]


class TestToolDetail:
    def test_found(self, client):
        r = client.get("/api/tools/ripgrep")
        assert r.status_code == 200
        body = r.get_json()
        assert body["name"] == "ripgrep" and body["category"] == "general"
        assert body["archived"] is False

    def test_not_found(self, client):
        assert client.get("/api/tools/does-not-exist").status_code == 404


class TestHybridFilterAndStaleness:
    @classmethod
    def setup_class(cls):
        mock = sys.modules.pop("backend.hybrid_search", None)
        from backend import hybrid_search
        cls.hs = hybrid_search
        if mock is not None:
            sys.modules["backend.hybrid_search"] = mock

    def test_allowed_filters_before_rerank(self, monkeypatch):
        docs = ["a scanner", "b scanner", "c scanner"]
        mk = lambda t: SimpleNamespace(page_content=t, metadata={})
        faiss = SimpleNamespace(similarity_search_with_score=lambda q, k: [(mk(d), 0.1) for d in docs])
        bm25 = SimpleNamespace(get_relevant_documents=lambda q: [mk(d) for d in docs])
        monkeypatch.setattr(self.hs, "_ensure_indexes", lambda dl: (bm25, faiss))
        seen = {}

        def fake_rerank(query, cands, top_k=10):
            seen["cands"] = [c.page_content for c in cands]
            return cands[:top_k]

        monkeypatch.setattr(self.hs, "rerank", fake_rerank)
        out = self.hs.search(docs, "scanner", allowed={"b scanner"})
        assert out == ["b scanner"] and seen["cands"] == ["b scanner"]

    def test_doc_list_hash_order_independent(self):
        assert self.hs.doc_list_hash(["a", "b"]) == self.hs.doc_list_hash(["b", "a"])
        assert self.hs.doc_list_hash(["a"]) != self.hs.doc_list_hash(["a", "b"])

    def test_stale_index_rebuilt_and_fresh_index_loaded(self, monkeypatch, tmp_path):
        calls = []

        class Store:
            def save_local(self, d):
                (tmp_path / "index.faiss").write_text("x")

        class FakeFAISS:
            @staticmethod
            def from_texts(docs, emb):
                calls.append("build")
                return Store()

            @staticmethod
            def load_local(*a, **k):
                calls.append("load")
                return Store()

        monkeypatch.setattr(self.hs, "FAISS", FakeFAISS)
        monkeypatch.setattr(self.hs, "FAISS_INDEX_PATH", str(tmp_path))
        self.hs.build_or_load_faiss_index(["one"])        # missing -> build
        self.hs.build_or_load_faiss_index(["one"])        # fresh -> load
        self.hs.build_or_load_faiss_index(["one", "two"])  # stale -> rebuild
        assert calls == ["build", "load", "build"]
        # an index whose vector size doesn't match the model is rebuilt even if the hash matches
        Store.index = SimpleNamespace(d=384)
        monkeypatch.setattr(self.hs, "_embedding_dim", lambda: 1024)
        calls.clear()
        self.hs.build_or_load_faiss_index(["one", "two"])
        assert calls == ["load", "load", "build"]
        meta = json.loads((tmp_path / "index_meta.json").read_text())
        assert meta["count"] == 2


def test_index_page_has_category_chips(client):
    html = client.get("/").get_data(as_text=True)
    for cat in ("all", "security", "general"):
        assert f'data-category="{cat}"' in html


def test_real_search_tool_passes_category_filter(monkeypatch):
    """backend.main.search_tool restricts hybrid search to the chosen category's docs."""
    mock = sys.modules.pop("backend.main", None)
    try:
        import backend.main as real_main
    finally:
        if mock is not None:
            sys.modules["backend.main"] = mock
    real_main.search_tool.cache_clear()
    real_main._tools = None
    seen = {}

    def fake_search(docs, query, allowed=None, **kw):
        seen["allowed"] = allowed
        return list(docs[:3]) if allowed is None else [d for d in docs if d in allowed][:3]

    monkeypatch.setattr(real_main, "search", fake_search)
    out = real_main.search_tool("scanner", "security")
    assert out and all(t["category"] == "security" for t in out)
    assert all("id" in t for t in out)
    general = real_main.search_tool("finder", "general")
    assert general and all(t["category"] == "general" for t in general)
    assert real_main.search_tool("scanner")[0]["id"]
    assert seen["allowed"] is None
    with pytest.raises(ValueError):
        real_main.search_tool("x", "games")
    real_main.search_tool.cache_clear()
    real_main._tools = None
