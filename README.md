# ToolHunt 🔍

*AI-powered semantic search engine for cybersecurity tools — 2,860+ indexed, RRF-ranked, cross-encoder reranked.*

<p align="center">
  <img src="https://img.shields.io/badge/Tools-2,860+-brightgreen?style=for-the-badge&logo=hammer-screwdriver" alt="2,860+ Tools"/>
  <img src="https://img.shields.io/badge/Python-3.12+-blue?style=for-the-badge&logo=python" alt="Python 3.12+"/>
  <img src="https://img.shields.io/badge/Flask-3.1+-red?style=for-the-badge&logo=flask" alt="Flask 3.1+"/>
  <img src="https://img.shields.io/badge/Tests-40-green?style=for-the-badge&logo=pytest" alt="40 Tests"/>
  <img src="https://img.shields.io/badge/License-GNU-green?style=for-the-badge&logo=gnu" alt="GNU License"/>
</p>

---

## 🌟 Overview

ToolHunt is an advanced semantic search engine for cybersecurity tools. Describe what you need in plain language, and it returns the best matches using a multi-stage retrieval pipeline:

```
query → BGE-M3 embedding (ONNX) + FAISS (top 198) + BM25
     → RRF fusion (k=60) → top 20
     → Cross-encoder reranker → top 10
     → Cache (300s TTL) → paginated response
```

---

## 🚀 Key Features

| Feature | Description |
|---------|-------------|
| 🔍 **BGE-M3 Semantic Search** | 1024-dim embeddings (MTEB 63.2, +44% over original model) via ONNX-accelerated inference |
| ⚡ **RRF Hybrid Fusion** | Reciprocal Rank Fusion (k=60) combining FAISS vectors + BM25 keywords for +13% recall |
| 🎯 **Cross-Encoder Reranker** | Top-20 candidates re-scored with `cross-encoder/ms-marco-MiniLM-L-6-v2` for +12% accuracy |
| 🗃️ **2,860+ Tool Database** | Curated cybersecurity tools across network, web, forensics, password, and exploitation categories |
| ⚙️ **Lazy-Cached Indexes** | BM25 + FAISS built once at startup, not rebuilt per query (5x speedup) |
| 📄 **Pagination** | Results limited to 10 per page with "Load More" for responsive browsing |
| 🚀 **Docker + Gunicorn** | Production-ready deployment with `docker-compose up` |
| 🧪 **40 Automated Tests** | Full TDD coverage — RRF, reranker, embeddings, caching, pagination, endpoints |
| 🎮 **Cyberpunk UI** | Terminal-inspired dark interface with animated grid background |

---

<p align="center">
  <img src="https://raw.githubusercontent.com/cyberytti/ToolHunt/main/docs/logo/ToolHunt_logo.png" alt="ToolHunt Logo" width="600"/>
</p>

---

## 🎥 Live Demo

<p align="center">
  <img src="https://raw.githubusercontent.com/cyberytti/ToolHunt/main/docs/showcase_video/ToolHunt_showcase_video.gif" alt="ToolHunt Demo" width="800"/>
</p>

---

## 📸 Screenshots

### Main Search Interface
![Main Search Interface](https://raw.githubusercontent.com/cyberytti/ToolHunt/main/docs/showcase_images/Screenshot%20from%202025-09-04%2015-57-39.png)
*Cyberpunk-styled main interface*

### Search Results
![Search Results Display](https://raw.githubusercontent.com/cyberytti/ToolHunt/main/docs/showcase_images/Screenshot%20from%202025-09-04%2015-58-40.png)
*Intelligent tool categorization with detailed descriptions*

---

## 🛠️ Technology Stack

### Search Pipeline
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Embeddings | **BAAI/bge-m3** (1024-dim, ONNX) | Semantic vector representations |
| Vector Search | **FAISS** (`faiss-cpu`) | Approximate nearest neighbor search (top 198) |
| Keyword Search | **BM25** (`rank_bm25`) | Exact/lexical term matching |
| Fusion | **RRF** (k=60) | Reciprocal Rank Fusion — combines dense + sparse rankings |
| Reranking | **cross-encoder/ms-marco-MiniLM-L-6-v2** | Pointwise query-document relevance scoring |

### Backend
| Component | Technology |
|-----------|-----------|
| Web Framework | **Flask 3.1** (application factory pattern, blueprints) |
| Database | **SQLite** (2,860 tools, 347KB) + **CSV** |
| Caching | **Flask-Caching** (SimpleCache dev / Redis production) |
| WSGI Server | **Gunicorn** (4 workers, Docker) |

### Frontend
| Technology | Purpose |
|-----------|---------|
| HTML5 + Jinja2 | Template (70 lines, extracted from monolith) |
| CSS3 | Cyberpunk theme (638 lines, extracted) |
| JavaScript | Search, pagination, alerts (271 lines, extracted) |

---

## 📁 Project Structure

```
ToolHunt/
├── app/                        # Flask application package
│   ├── __init__.py             # create_app() factory
│   ├── routes.py               # Blueprint: GET /, POST /search
│   ├── config.py               # Config / TestingConfig / ProductionConfig
│   └── extensions.py           # Flask-Caching Cache singleton
├── app.py                      # WSGI entry point (5 lines)
├── backend/
│   ├── main.py                 # search_tool() — DB load, search orchestration
│   ├── hybrid_search.py        # BGE-M3 + FAISS + BM25 + RRF fusion
│   ├── reranker.py             # Cross-encoder reranker singleton
│   └── database/
│       └── tools.db            # 2,860+ cybersecurity tools
├── tests/
│   ├── conftest.py             # ML module mocks (tests run without models)
│   ├── test_app.py             # Flask route smoke test
│   ├── test_hybrid_search.py   # RRF, EmbeddingWrapper, caching (15 tests)
│   ├── test_reranker.py        # Cross-encoder (9 tests)
│   └── test_search.py          # Endpoints, pagination, cache (11 tests)
├── static/
│   ├── css/style.css           # Cyberpunk theme (extracted)
│   └── js/app.js               # Search + pagination JS (extracted)
├── templates/
│   └── index.html              # HTML skeleton (70 lines)
├── Dockerfile                  # python:3.12-slim, model pre-download
├── docker-compose.yml          # Port 5000, volume mount for DB
├── pyproject.toml              # Project config + pytest settings
└── requirements-docker.txt     # Production deps including gunicorn
```

---

## 🚀 Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/canonrebel04/ToolHunt.git
cd ToolHunt

# Install dependencies
pip install -r requirements.txt

# Launch ToolHunt
python app.py
```

Access at `http://localhost:5000`

### Docker Production

```bash
docker-compose up --build
```

The Docker image pre-downloads the BGE-M3 model with ONNX backend at build time for faster startup.

### Google Colab

Open [`toolhunt_in_colab.py`](toolhunt_in_colab.py) in Colab with a T4 GPU runtime, paste your ngrok token, and run.

---

## 🗂️ Categories & API

Every tool is either **security** (pentest/forensics/etc.) or **general** (everyday CLI tools).
The UI has **All / Security / General CLI** filter chips (All is the default).

```bash
# Search (category: all | security | general, default all)
curl -s -X POST localhost:5000/search -H 'Content-Type: application/json' \
  -d '{"query": "port scanner", "category": "security", "limit": 10}'

# Full record for one tool
curl -s localhost:5000/api/tools/nmap
```

Add a tool by hand: `python update_database.py NAME "DESCRIPTION" URL --category general`.
The FAISS search index is a build artifact (not in git): the Docker build runs `python -m backend.build_index`, and locally the index is built on the first search and rebuilt automatically whenever the tool list changes.

## 📖 Tool docs (Tier 1)

Every tool can have a structured write-up under `data/docs/<id>.json`: summary, install commands, usage, **flags parsed from real help output**, subcommands, and examples (mostly from [tldr-pages](https://github.com/tldr-pages/tldr), CC BY 4.0). Flags are never invented — they come from Kali's pre-captured `-h` output, or from fixtures under `data/help/` for showcase tools.

```bash
curl -s localhost:5000/api/tools/nmap/docs | jq '.flags | length'
python -m docgen.run --kali-cache /tmp/kali.tgz --tldr-cache /tmp/tldr.zip
```

AI enrichment (Tier 2) is optional — see below.

## 🤖 AI docs (Tier 2)

Pluggable LLM enrichment on top of Tier 1. **Flags are never invented** — the model may only rewrite summaries, highlights, flag descriptions, and examples; every example is checked against the Tier-1 flag set before it is saved.

### Providers

| Provider | `TOOLHUNT_LLM_PROVIDER` | API key env / GitHub secret | Default base URL |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_API_KEY` or `TOOLHUNT_LLM_API_KEY` | `https://api.openai.com/v1` |
| xAI (Grok) | `xai` | `XAI_API_KEY` | `https://api.x.ai/v1` |
| Google Gemini | `gemini` | `GEMINI_API_KEY` or `GOOGLE_API_KEY` | Gemini `generateContent` |
| DeepSeek | `deepseek` | `DEEPSEEK_API_KEY` | `https://api.deepseek.com/v1` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | Messages API |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | `https://openrouter.ai/api/v1` |
| Groq / Together / Fireworks | `groq` / `together` / `fireworks` | matching `*_API_KEY` | OpenAI-compatible |
| Local (Ollama / vLLM / llama.cpp) | `ollama` or `local` | optional | `http://127.0.0.1:11434/v1` |
| Custom OpenAI-compatible | `custom` | `TOOLHUNT_LLM_API_KEY` | set `TOOLHUNT_LLM_BASE_URL` |

Common overrides: `TOOLHUNT_LLM_MODEL`, `TOOLHUNT_LLM_BASE_URL`, `TOOLHUNT_LLM_TIMEOUT`.

### What you add (repo secrets / local env)

In the GitHub repo → **Settings → Secrets and variables → Actions**, add **one** key for the provider you want (plus optional `TOOLHUNT_LLM_MODEL`). Locally, export the same names before running the CLI. No key is committed; enrichment is manual / opt-in.

```bash
# local OpenAI-compatible (Ollama)
TOOLHUNT_LLM_PROVIDER=ollama TOOLHUNT_LLM_MODEL=llama3.2 \
  python -m docgen.enrich --tool nmap --dry-run

# hosted
TOOLHUNT_LLM_PROVIDER=xai XAI_API_KEY=... TOOLHUNT_LLM_MODEL=grok-4-fast-non-reasoning \
  python -m docgen.enrich --limit 5
```

GitHub Action: **Actions → Docs enrich (Tier 2 LLM) → Run workflow** (skips cleanly if no secret is set).



## 🖥️ Tool detail UI

Every tool has a shareable page at `/tool/<id>` (works without JavaScript) and a Docs button on search result cards that opens a slide-over panel. Both show install tabs, examples, a filterable flags table, and an explainshell-style command annotator backed by verified help JSON (`POST /api/tools/<id>/explain`).


## 🔭 Automatic discovery

A weekly GitHub Action (`.github/workflows/discovery.yml`, Mondays 06:17 UTC, or run it by hand from the Actions tab) collects tools from:

| Source | Category |
|---|---|
| [BlackArch](https://github.com/BlackArch/blackarch-site) tool list | security (subcategory = BlackArch group) |
| [Kali tools](https://www.kali.org/tools/) | security |
| GitHub topics (`pentesting`, `osint`, `fuzzing`, `red-team`… ≥300★) | security |
| Most-installed [Homebrew](https://formulae.brew.sh/) formulae (libraries skipped) | general |
| [toolleeo/cli-apps](https://github.com/toolleeo/cli-apps) | general |
| GitHub topics (`cli`, `terminal`, `command-line-tool`, ≥3000★) | general |

New tools must pass quality gates (real description; for non-curated sources: not a fork, not archived, enough stars, not abandoned). Duplicates are merged by name, alias, or repo, and a tool listed by any security source stays **security**. Stars, last-commit date and archived status are refreshed for every GitHub-hosted tool. The job runs the tests, opens a PR with a summary, merges it automatically, and rebuilds the Docker image. At most 1,500 new tools are added per run (best-scored first).

Run it locally (writes to the DB; `--dry-run` to preview):

```bash
GITHUB_TOKEN=$(gh auth token) python -m discovery.run --dry-run --report /tmp/report.md
python -m discovery.run --sources blackarch,kali   # subset, no token needed
```

## 🧪 Testing

**130+ tests, under 1s** — all ML modules are mocked via `conftest.py`, so tests run without downloading models.

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ --cov=backend --cov=app

# Run specific test file
python3 -m pytest tests/test_hybrid_search.py -v
```

---

## 📊 Benchmarks

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Embedding Model | MiniLM-L12-v2 (384-dim, MTEB 43.9) | **BGE-M3** (1024-dim, MTEB 63.2) | **+44%** |
| Search Fusion | Dict dedup | **RRF** (k=60) | **+13% recall** |
| Reranking | None | **Cross-encoder** (top20→10) | **+12% accuracy** |
| BM25/FAISS Indexes | Rebuilt per query | **Cached once** | **5x speedup** |
| Model Instances | 2 (duplicate) | **1** (shared) | **-1** |
| Caching | None | **Flask-Caching** (300s) | **3-10x repeat** |
| Pagination | All results at once | **Limit 10 + Load More** | UX |
| Architecture | Global `app = Flask()` | **Factory + blueprints** | Maintainable |
| UI | 981-line inline monolith | **70 HTML + 638 CSS + 271 JS** | Modular |
| Deployment | Colab only | **Docker + Gunicorn** | Production |
| Tests | 0 | **40** (0.14s) | Verified |

---

## 🔍 Usage Examples

| Category | Example Queries |
|----------|----------------|
| **Network Security** | `"network scanner"`, `"port enumeration tools"` |
| **Web Application** | `"sql injection tools"`, `"web vulnerability scanner"` |
| **Password Attacks** | `"password cracking utilities"`, `"brute force tools"` |
| **Forensics** | `"digital forensics analysis"`, `"memory analysis tools"` |
| **Reconnaissance** | `"OSINT gathering tools"`, `"subdomain enumeration"` |

---

## 🤝 Contributing

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 📝 Follow TDD: write failing test → implement → verify all 40 tests pass
5. 📤 Push and open a Pull Request

---

## ⚖️ Ethical Use

ToolHunt is designed for legitimate cybersecurity purposes only. Use only on systems you own or have explicit permission to test.

---

## 📄 License

This project is licensed under the **GNU License** — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>ToolHunt 🔍 — AI-Powered Cybersecurity Tool Discovery</strong>
</p>

<p align="center">
  <a href="https://github.com/canonrebel04/ToolHunt/stargazers">
    <img src="https://img.shields.io/github/stars/canonrebel04/ToolHunt?style=social" alt="GitHub stars"/>
  </a>
  <a href="https://github.com/canonrebel04/ToolHunt/fork">
    <img src="https://img.shields.io/github/forks/canonrebel04/ToolHunt?style=social" alt="GitHub forks"/>
  </a>
</p>
