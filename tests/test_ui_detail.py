"""Phase 3: tool detail page, command explainer, docs panel APIs."""
import json

from app.explain import explain_command, tokenize


class TestExplainUnit:
    def test_tokenize_quotes(self):
        assert tokenize('nmap -p 80 "host name"') == ["nmap", "-p", "80", "host name"]

    def test_flag_and_subcommand(self):
        doc = {
            "name": "ab-av1",
            "flags": [
                {"name": "--thorough", "short": "", "aliases": [], "arg": "", "description": "Exhaustive CRF search", "example": ""},
                {"name": "--input", "short": "-i", "aliases": [], "arg": "<FILE>", "description": "Input video", "example": ""},
            ],
            "subcommands": [{"name": "auto-encode", "description": "Find CRF and encode"}],
        }
        out = explain_command("ab-av1 auto-encode --thorough -i movie.mkv", doc)
        kinds = [t["kind"] for t in out["tokens"]]
        assert kinds == ["binary", "subcommand", "flag", "flag", "flag_arg"]
        assert out["tokens"][2]["note"] == "Exhaustive CRF search"
        assert out["unknown_flags"] == []

    def test_unknown_flag(self):
        doc = {"flags": [{"name": "--help", "short": "-h", "aliases": [], "arg": "", "description": "help"}]}
        out = explain_command("tool --nope", doc)
        assert out["tokens"][1]["kind"] == "unknown_flag"
        assert out["unknown_flags"] == ["--nope"]

    def test_bundled_shorts(self):
        doc = {
            "flags": [
                {"name": "", "short": "-s", "aliases": [], "arg": "", "description": "syn"},
                {"name": "", "short": "-V", "aliases": [], "arg": "", "description": "version detect"},
            ]
        }
        out = explain_command("nmap -sV target", doc)
        assert [t["kind"] for t in out["tokens"]] == ["binary", "flag", "flag", "arg"]


class TestToolPage:
    def test_page_renders(self, client):
        r = client.get("/tool/ripgrep")
        assert r.status_code == 200
        html = r.get_data(as_text=True)
        assert "ripgrep" in html
        assert "Command explainer" in html
        assert "flagFilter" in html or "Flags" in html
        # XSS posture: raw angle brackets from description must be escaped if present
        assert "<script>" not in html.lower() or "&lt;script&gt;" in html.lower()

    def test_missing_tool(self, client):
        r = client.get("/tool/does-not-exist-xyz")
        assert r.status_code == 404
        assert b"not found" in r.data.lower()

    def test_index_has_docs_panel_shell(self, client):
        html = client.get("/").get_data(as_text=True)
        assert 'id="docsPanel"' in html
        assert "docs-btn" in client.get("/static/js/app.js").get_data(as_text=True)


class TestExplainApi:
    def test_explain_ab_av1(self, client):
        # real docs on disk; tool exists in mock DB as ab-av1
        r = client.post(
            "/api/tools/ab-av1/explain",
            data=json.dumps({"command": "ab-av1 auto-encode --thorough -i video.mkv"}),
            content_type="application/json",
        )
        assert r.status_code == 200
        body = r.get_json()
        assert body["tokens"][0]["kind"] == "binary"
        kinds = {t["kind"] for t in body["tokens"]}
        assert "flag" in kinds or "subcommand" in kinds

    def test_explain_empty(self, client):
        r = client.post("/api/tools/nmap/explain", data=json.dumps({"command": ""}), content_type="application/json")
        assert r.status_code == 400

    def test_explain_missing_tool(self, client):
        r = client.post(
            "/api/tools/nope-xyz/explain",
            data=json.dumps({"command": "nope --help"}),
            content_type="application/json",
        )
        assert r.status_code == 404
