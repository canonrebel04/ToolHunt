"""Shared fixtures for ToolHunt test suite.

Mocks the heavy ML/search backend so tests run fast without models or dependencies.
"""

import sys
import types

import pytest

# ── Mock heavy backend modules before app.py is imported ──────────────

_MOCK_TOOLS = [
    ("nmap", "Network discovery and security scanning tool", "https://nmap.org", "security", "Network"),
    ("sqlmap", "Automatic SQL injection and database takeover tool", "https://sqlmap.org", "security", "Web"),
    ("metasploit", "Penetration testing framework", "https://metasploit.com", "security", "Exploitation"),
    ("burpsuite", "Web application security testing platform", "https://portswigger.net", "security", "Web"),
    ("wireshark", "Network protocol analyzer", "https://wireshark.org", "security", "Network"),
    ("john", "Password cracking tool", "https://openwall.com/john", "security", "Password"),
    ("hydra", "Parallelized network login cracker", "https://github.com/vanhauser-thc/thc-hydra", "security", "Password"),
    ("aircrack-ng", "WiFi security auditing suite", "https://aircrack-ng.org", "security", "Network"),
    ("gobuster", "Directory/file enumeration tool", "https://github.com/OJ/gobuster", "security", "Web"),
    ("nikto", "Web server vulnerability scanner", "https://cirt.net/Nikto2", "security", "Vulnerability"),
    ("hashcat", "Advanced password recovery tool", "https://hashcat.net", "security", "Password"),
    ("openvas", "Open-source vulnerability scanner", "https://openvas.org", "security", "Vulnerability"),
    ("volatility", "Memory forensics framework", "https://volatilityfoundation.org", "security", "Forensics"),
    ("ripgrep", "Recursively search directories for a regex pattern", "https://github.com/BurntSushi/ripgrep", "general", "Files"),
    ("ab-av1", "AV1 video encoding with automatic VMAF-targeted crf search", "https://github.com/alexheretic/ab-av1", "general", "Media"),
]

MOCK_TOOL_DICTS = [
    {"id": n, "name": n, "description": d, "url": u, "category": c, "subcategory": sc,
     "repo_url": "", "tags": [], "sources": ["test"], "language": "", "license": "",
     "stars": None, "last_commit": "", "archived": 0, "first_seen": "", "updated_at": ""}
    for n, d, u, c, sc in _MOCK_TOOLS
]


class _MockSearchTool:
    """Stand-in for backend.main.search_tool that returns canned results."""

    def __call__(self, query, category="all"):
        return [t for t in MOCK_TOOL_DICTS if category == "all" or t["category"] == category]


def _mock_get_tool(tool_id):
    return next((dict(t) for t in MOCK_TOOL_DICTS if t["id"] == tool_id), None)


def _build_fake_module(name, attrs=None):
    """Create a fake module that pytest's sys.path will find before the real one."""
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    return mod


# Mock backend.main (the module-level code loads models, DB, etc.)

_mock_main = _build_fake_module("backend.main", {
    "search_tool": _MockSearchTool(),
    "get_tool": _mock_get_tool,
    "search": lambda q: [],
    "find_indices": lambda p, q: [],
    "_load_tools": lambda: None,
    "_tools": [],
})


# Mock backend.hybrid_search
_mock_hybrid = _build_fake_module("backend.hybrid_search", {
    "search": lambda doc_list, query, similarity_threshold=0.5, allowed=None, top_k=10: [],
    "build_or_load_faiss_index": lambda doc_list, force_rebuild=False: None,
    "model": type("FakeST", (), {})(),
})

# Mock langchain_community.vectorstores / retrievers
class _FakeFAISSInstance:
    """Mimics a FAISS vectorstore instance with the methods search() uses."""
    def similarity_search_with_score(self, query, k):
        # Return empty results: each result is (Document, distance)
        # We need to import Document here since it's what search() returns
        return []

    def save_local(self, folder_path, **kwargs):
        pass

class _FakeFAISS:
    """Mimics the FAISS class with load_local and from_texts classmethods."""
    @classmethod
    def load_local(cls, *a, **kw):
        return _FakeFAISSInstance()
    @classmethod
    def from_texts(cls, *a, **kw):
        return _FakeFAISSInstance()

_mock_lc_community = types.ModuleType("langchain_community")
_mock_faiss = types.ModuleType("langchain_community.vectorstores")
_mock_faiss.FAISS = _FakeFAISS
_mock_bm25 = types.ModuleType("langchain_community.retrievers")


class _FakeBM25Instance:
    """Mimics a BM25 retriever instance with the methods search() uses."""
    def get_relevant_documents(self, query):
        return []


class _FakeBM25:
    """Mimics the BM25Retriever class with from_texts classmethod."""
    @classmethod
    def from_texts(cls, texts):
        return _FakeBM25Instance()


_mock_bm25.BM25Retriever = _FakeBM25
_mock_lc_community.vectorstores = _mock_faiss
_mock_lc_community.retrievers = _mock_bm25

# Mock sentence_transformers
class _FakeNumpyArray:
    """Mimics numpy array's tolist() method for test mocks."""
    def __init__(self, data):
        self.data = data
    def tolist(self):
        return self.data

class _FakeCrossEncoder:
    """Mimics CrossEncoder for testing without loading real models."""
    def __init__(self, model_name, **kwargs):
        self.model_name = model_name

    def predict(self, pairs):
        """Return deterministic scores for testability.

        Returns a score for each pair as 0.9 minus a small decay
        based on position.  Tests can override this return value
        via unittest.mock.patch.object for precise assertions.
        """
        # Use a hash of the document text for deterministic but
        # varied scores, so ordering tests are meaningful.
        scores = []
        for query, doc_text in pairs:
            # Simple deterministic score based on document text
            h = hash(doc_text) % 100
            scores.append(50 + h / 2.0)  # range ~0-100
        return scores


_mock_st = types.ModuleType("sentence_transformers")
_mock_st.SentenceTransformer = type("FakeST", (), {
    "__init__": lambda self, *a, **kw: None,
    "encode": lambda self, text: _FakeNumpyArray([0.1] * 1024) if isinstance(text, str) else _FakeNumpyArray([[0.1] * 1024 for _ in text]),
    "encode_query": lambda self, q: [0.1] * 1024,
    "encode_document": lambda self, docs: [[0.1] * 1024 for _ in docs],
    "similarity": lambda self, a, b: [[0.85]],
})
_mock_st.CrossEncoder = _FakeCrossEncoder

# Register all mocks in sys.path so they intercept the imports
_MODULE_MOCKS = {
    "backend.main": _mock_main,
    "backend.hybrid_search": _mock_hybrid,
    "langchain_community": _mock_lc_community,
    "langchain_community.vectorstores": _mock_faiss,
    "langchain_community.retrievers": _mock_bm25,
    "sentence_transformers": _mock_st,
}


# ── Keep the real data files out of reach ─────────────────────────────
# Tests read a *copy* of tools.db and write any FAISS index to a temp dir.
# pytest_sessionfinish also fails the run if the real files changed anyway.
import hashlib
import os
import shutil
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_PROTECTED = [
    _REPO / "backend" / "database" / "tools.db",
    _REPO / "backend" / "faiss_index" / "index.faiss",
    _REPO / "backend" / "faiss_index" / "index.pkl",
    _REPO / "backend" / "faiss_index" / "index_meta.json",
]
_TMP = Path(tempfile.mkdtemp(prefix="toolhunt-tests-"))


def _fingerprint():
    return {str(p): (hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None) for p in _PROTECTED}


def pytest_configure(config):
    """Insert mock modules before any test collection; point data paths at temp copies."""
    config._toolhunt_fp = _fingerprint()
    real_db = _REPO / "backend" / "database" / "tools.db"
    if real_db.exists():
        shutil.copy(real_db, _TMP / "tools.db")
    os.environ["TOOLHUNT_DB"] = str(_TMP / "tools.db")
    os.environ["TOOLHUNT_INDEX_DIR"] = str(_TMP / "faiss_index")
    os.environ.setdefault("TOOLHUNT_DOCS_DIR", str(_REPO / "data" / "docs"))
    for name, mod in _MODULE_MOCKS.items():
        sys.modules[name] = mod


def pytest_sessionfinish(session, exitstatus):
    before = getattr(session.config, "_toolhunt_fp", None)
    shutil.rmtree(_TMP, ignore_errors=True)
    if before is not None and _fingerprint() != before:
        changed = [p for p, h in _fingerprint().items() if before.get(p) != h]
        print(f"\nERROR: tests modified real data files: {changed}")
        session.exitstatus = 1


# ── Flask test client fixture ────────────────────────────────────────

@pytest.fixture
def app():
    """Provide the Flask application instance created via factory (with mocked search backend)."""
    from app import create_app
    from app.config import TestingConfig
    flask_app = create_app(TestingConfig)
    return flask_app


@pytest.fixture
def client(app):
    """Provide a Flask test client for HTTP-level tests."""
    with app.test_client() as c:
        yield c
