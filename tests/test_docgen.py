"""Offline tests for Tier 1 doc generation."""
import json
from pathlib import Path

from docgen import build, helpparse, kali, schema, tldr

CLAP = """\
Usage: feroxbuster [OPTIONS]

Options:
  -u, --url <URL>          The target URL (required)
  -w, --wordlist <FILE>    Path to the wordlist [default: wordlist.txt]
  -t, --threads <THREADS>  Number of concurrent threads [default: 50]
  -v, --verbosity...       Increase verbosity
  -h, --help               Print help
  -V, --version            Print version
"""

COBRA = """\
Usage:
  gobuster [command]

Available Commands:
  dir         Uses directory/file enumeration mode
  dns         Uses DNS subdomain enumeration mode
  help        Help about any command

Flags:
  -h, --help      help for gobuster
  -v, --version   version for gobuster
"""

ARGPARSE = """\
usage: sqlmap [options]

options:
  -h, --help            show this help message and exit
  -u URL, --url=URL     Target URL
  --batch               Never ask for user input
  -v VERBOSE            Verbosity level: 0-6 (default 1)
"""

NMAP = """\
Nmap 7.94 ( https://nmap.org )
Usage: nmap [Scan Type(s)] [Options] {target specification}
TARGET SPECIFICATION:
  -iL <inputfilename>: Input from list of hosts/networks
  -iR <num hosts>: Choose random targets
  --exclude <host1[,host2][,host3],...>: Exclude hosts/networks
HOST DISCOVERY:
  -sL: List Scan - simply list targets to scan
  -sn: Ping Scan - disable port scan
  -Pn: Treat all hosts as online -- skip host discovery
"""


def test_parse_clap_style():
    p = helpparse.parse_help(CLAP, "feroxbuster")
    assert p["usage"].startswith("feroxbuster")
    by = {f["name"]: f for f in p["flags"]}
    assert by["--url"]["short"] == "-u" and by["--url"]["arg"] == "<URL>"
    assert by["--wordlist"]["default"] == "wordlist.txt"
    assert by["--threads"]["example"] == "feroxbuster --threads <THREADS>"


def test_parse_cobra_subcommands():
    p = helpparse.parse_help(COBRA, "gobuster")
    assert {s["name"] for s in p["subcommands"]} >= {"dir", "dns"}
    assert any(f["name"] == "--help" for f in p["flags"])


def test_parse_argparse_and_nmap():
    p = helpparse.parse_help(ARGPARSE, "sqlmap")
    by = {f["name"]: f for f in p["flags"]}
    assert by["--url"]["short"] == "-u" and by["-v"]["default"] == "1"
    p = helpparse.parse_help(NMAP, "nmap")
    names = {f["name"] for f in p["flags"]}
    assert {"-iL", "-iR", "--exclude", "-sL", "-sn", "-Pn"} <= names


def test_hashcat_table_format():
    text = """\
-m, --hash-type=NUM             | Num  | Hash-type | -m 1000
-a, --attack-mode=NUM           | Num  | Attack-mode | -a 3
"""
    p = helpparse.parse_help(text, "hashcat")
    by = {f["name"]: f for f in p["flags"]}
    assert by["--hash-type"]["short"] == "-m"
    assert "1000" in by["--hash-type"]["example"]


def test_flags_in_command_and_known():
    assert helpparse.flags_in_command("rg -i --glob '*.py' foo") == ["-i", "--glob"]
    known = helpparse.known_flag_names([{"name": "--glob", "short": "-g", "aliases": []}])
    assert "-g" in known and "--glob" in known


def test_build_validates_examples_against_help():
    doc = build.from_help("demo", "demo", CLAP, binary="feroxbuster", tldr={
        "name": "feroxbuster", "path": "pages/common/feroxbuster.md",
        "description": "Fast content discovery",
        "examples": [
            {"cmd": "feroxbuster -u https://ex.com -w words.txt", "explanation": "basic"},
            {"cmd": "feroxbuster --not-a-real-flag", "explanation": "bogus"},
        ],
    }, description="Fast scanner", help_source="test")
    assert doc["verified"]["flags_from_help"]
    cmds = [e["cmd"] for e in doc["examples"]]
    assert "feroxbuster -u https://ex.com -w words.txt" in cmds
    assert "feroxbuster --not-a-real-flag" not in cmds
    assert doc["install"] == []


def test_kali_help_blocks_and_install():
    md = """---
Title: demo
Homepage: https://example.com
Metapackages: kali-tools-web
PackagesInfo: |
 ### demo
 **A demo tool**
 **How to install:** `sudo apt install demo`
 ##### demo
 ```
 root@kali:~# demo -h
 Usage: demo [options]
   -h, --help   help
 ```
---
"""
    blocks = kali.help_blocks(md)
    assert blocks[0]["binary"] == "demo" and "Usage: demo" in blocks[0]["output"]
    assert kali.install_commands(md, "demo") == ["sudo apt install demo"]
    assert kali.best_block(blocks, "demo")["binary"] == "demo"


def test_tldr_parse_and_render():
    md = """# rg

> Ripgrep, a recursive search tool.

- Search for a pattern:

`rg {{pattern}}`

- Literal string:

`rg {{[-F|--fixed-strings]}} -- {{string}}`
"""
    page = tldr.parse_page(md)
    assert page["name"] == "rg"
    assert page["examples"][0]["cmd"] == "rg <pattern>"
    assert page["examples"][1]["cmd"] == "rg --fixed-strings -- <string>"


def test_schema_roundtrip(tmp_path):
    doc = schema.empty_doc("nmap", "Nmap")
    doc["summary"] = "scanner"
    schema.save_doc(doc, tmp_path)
    assert schema.load_doc("nmap", tmp_path)["summary"] == "scanner"


def test_committed_showcase_docs_exist():
    root = Path(__file__).resolve().parents[1] / "data" / "docs"
    for tid in ("nmap", "ripgrep", "ab-av1", "nuclei", "hashcat"):
        p = root / f"{tid}.json"
        assert p.is_file(), tid
        doc = json.loads(p.read_text())
        assert doc["id"] == tid
        if tid == "ab-av1":
            assert any("auto-encode" in e["cmd"] for e in doc["examples"])
            assert any(f["name"] == "--thorough" for f in doc["flags"])
        if tid == "ripgrep":
            assert len(doc["flags"]) >= 50
        if tid == "nmap":
            assert doc["verified"]["flags_from_help"] and len(doc["flags"]) >= 40


def test_docs_api(client):
    r = client.get("/api/tools/nmap/docs")
    assert r.status_code == 200
    body = r.get_json()
    assert body["id"] == "nmap" and len(body["flags"]) >= 40
    assert client.get("/api/tools/no-such-tool-xyz/docs").status_code == 404
