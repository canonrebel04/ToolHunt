"""Tier-2 LLM enrichment: merge validation + provider config (no live API calls)."""
import json

import pytest

from docgen.llm.enrich import enrich_doc, merge_enrichment
from docgen.llm.providers import LLMConfig, chat_completion, list_providers

BASE = {
    "id": "demo",
    "name": "demo",
    "schema_version": 1,
    "summary": "short",
    "highlights": [],
    "install": [{"method": "brew", "cmd": "brew install demo"}],
    "usage": "demo [OPTIONS]",
    "subcommands": [],
    "flags": [
        {"name": "--input", "short": "-i", "aliases": [], "arg": "<FILE>", "required": False,
         "description": "Input file", "default": "", "example": "demo -i f"},
        {"name": "--thorough", "short": "", "aliases": [], "arg": "", "required": False,
         "description": "Be thorough", "default": "", "example": "demo --thorough"},
    ],
    "examples": [{"cmd": "demo -i a", "explanation": "basic", "source": "tldr"}],
    "see_also": [],
    "sources": ["captured-help"],
    "verified": {"flags_from_help": True, "examples_from_tldr": True},
}


class TestMerge:
    def test_locks_flag_identity(self):
        llm = {
            "summary": "A longer summary about demo.",
            "highlights": ["Fast", "Thorough mode"],
            "flags": [
                {"name": "--input", "description": "Path to the input media file.", "example": "demo --input movie.mkv"},
                {"name": "--invented", "description": "should be ignored", "example": "demo --invented"},
            ],
            "examples": [
                {"cmd": "demo --thorough -i movie.mkv", "explanation": "Thorough encode"},
                {"cmd": "demo --nope", "explanation": "bad flag dropped"},
            ],
            "see_also": ["ffmpeg"],
        }
        out = merge_enrichment(BASE, llm, provider="openai", model="gpt-test")
        assert out["summary"].startswith("A longer")
        assert out["highlights"] == ["Fast", "Thorough mode"]
        assert out["flags"][0]["name"] == "--input"
        assert out["flags"][0]["arg"] == "<FILE>"
        assert "media file" in out["flags"][0]["description"]
        assert all(f["name"] != "--invented" for f in out["flags"])
        cmds = [e["cmd"] for e in out["examples"]]
        assert "demo --thorough -i movie.mkv" in cmds
        assert "demo --nope" not in cmds
        assert out["install"] == BASE["install"]
        assert out["verified"]["llm_enriched"] is True
        assert any(s.startswith("llm:openai:") for s in out["sources"])

    def test_enrich_doc_with_fake_chat(self):
        payload = {
            "summary": "Enriched summary.",
            "highlights": ["Chip"],
            "flags": [{"name": "--thorough", "description": "Exhaustive search.", "example": "demo --thorough"}],
            "examples": [{"cmd": "demo --thorough", "explanation": "Go deep"}],
            "see_also": [],
        }

        def fake_chat(messages, config=None, temperature=0.2):
            assert messages[0]["role"] == "system"
            return json.dumps(payload)

        cfg = LLMConfig(provider="openai", model="x", api_key="k", base_url="http://example", kind="openai")
        out = enrich_doc(BASE, config=cfg, chat=fake_chat)
        assert out["summary"] == "Enriched summary."
        assert out["flags"][1]["description"] == "Exhaustive search."


class TestProviders:
    def test_list_includes_requested(self):
        names = set(list_providers())
        for n in ("openai", "xai", "gemini", "deepseek", "anthropic", "openrouter", "ollama", "local"):
            assert n in names

    def test_from_env_openai(self, monkeypatch):
        monkeypatch.setenv("TOOLHUNT_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("TOOLHUNT_LLM_MODEL", raising=False)
        cfg = LLMConfig.from_env()
        assert cfg.provider == "openai" and cfg.api_key == "sk-test"
        assert "openai.com" in cfg.base_url

    def test_from_env_local_no_key(self, monkeypatch):
        monkeypatch.setenv("TOOLHUNT_LLM_PROVIDER", "ollama")
        monkeypatch.delenv("TOOLHUNT_LLM_API_KEY", raising=False)
        monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
        cfg = LLMConfig.from_env()
        assert cfg.provider == "ollama" and cfg.kind == "openai"

    def test_from_env_missing_key(self, monkeypatch):
        monkeypatch.setenv("TOOLHUNT_LLM_PROVIDER", "xai")
        for k in ("XAI_API_KEY", "TOOLHUNT_LLM_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(ValueError, match="API key"):
            LLMConfig.from_env()

    def test_openai_chat_posts_json(self, monkeypatch):
        cfg = LLMConfig(provider="openai", model="gpt-x", api_key="sk", base_url="https://api.openai.com/v1", kind="openai")
        captured = {}

        class Resp:
            def read(self):
                return json.dumps({"choices": [{"message": {"content": '{"ok":true}'}}]}).encode()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        def fake_urlopen(req, timeout=0):
            captured["url"] = req.full_url
            captured["body"] = json.loads(req.data.decode())
            captured["auth"] = req.headers.get("Authorization")
            return Resp()

        monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
        text = chat_completion([{"role": "user", "content": "hi"}], config=cfg)
        assert text == '{"ok":true}'
        assert captured["url"].endswith("/chat/completions")
        assert captured["body"]["model"] == "gpt-x"
        assert captured["auth"] == "Bearer sk"
