#!/usr/bin/env python3
"""
End-to-end test harness for the mcp-server.

Spawns the server via stdio for each test, sends a JSON-RPC request,
asserts on the response. Exits non-zero on any failure.

Run: python3 test-e2e.py
"""

import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER = REPO_ROOT / "mcp-server" / "dist" / "index.js"

failures = []
passes = 0


def call(data_dir: str, name: str, args: dict[str, Any]) -> str:
    """Call a tool, return the text content of the first result."""
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": args},
    }
    proc = subprocess.run(
        ["node", str(SERVER), "--data-dir", data_dir],
        input=json.dumps(req) + "\n",
        capture_output=True,
        text=True,
        timeout=15,
    )
    out = proc.stdout.strip()
    if not out:
        return f"<empty stdout, stderr={proc.stderr.strip()}>"
    try:
        resp = json.loads(out)
    except Exception as e:
        return f"<invalid JSON response: {e}; raw={out[:200]}>"
    if "error" in resp:
        return f"<rpc-error: {resp['error']}>"
    try:
        return resp["result"]["content"][0]["text"]
    except (KeyError, IndexError):
        return f"<malformed result: {out[:200]}>"


def list_tools(data_dir: str) -> list[str]:
    req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    proc = subprocess.run(
        ["node", str(SERVER), "--data-dir", data_dir],
        input=json.dumps(req) + "\n",
        capture_output=True,
        text=True,
        timeout=10,
    )
    resp = json.loads(proc.stdout.strip())
    return [t["name"] for t in resp["result"]["tools"]]


def assertion(label: str, condition: bool, detail: str = "") -> None:
    global passes
    if condition:
        passes += 1
        print(f"  PASS  {label}")
    else:
        failures.append((label, detail))
        print(f"  FAIL  {label} :: {detail}")


def setup_tmpdir() -> str:
    d = tempfile.mkdtemp(prefix="org-mcp-e2e-")
    for sub in ("sources", "nodes/units", "nodes/people", "identity", "language", "commitments"):
        (Path(d) / sub).mkdir(parents=True, exist_ok=True)
    return d


def teardown_tmpdir(d: str) -> None:
    shutil.rmtree(d, ignore_errors=True)


def run_section(label: str, fn) -> None:
    print(f"\n--- {label} ---")
    fn()


# ============================================================================
# Test sections
# ============================================================================

def test_tools_listing():
    d = setup_tmpdir()
    try:
        names = list_tools(d)
        assertion("12 tools registered", len(names) == 12, f"got {len(names)}: {names}")
        for expected in ("org_read", "org_search", "org_list", "org_neighbors",
                         "org_write_node", "org_save_source", "org_log_append",
                         "org_skills_list", "org_skill_read", "org_lint_run",
                         "org_play_run", "org_open"):
            assertion(f"tool '{expected}' present", expected in names)
    finally:
        teardown_tmpdir(d)


def test_org_log_append():
    d = setup_tmpdir()
    try:
        # Plain entry
        out = call(d, "org_log_append", {"entry": "hello world"})
        parsed = json.loads(out)
        assertion("log_append plain entry ok", parsed.get("ok") is True, out)
        assertion("log_append has date prefix", parsed["line"].startswith("20"), out)

        # Custom date
        out = call(d, "org_log_append", {"entry": "backdated", "date": "2025-01-15"})
        parsed = json.loads(out)
        assertion("log_append custom date", parsed["line"].startswith("2025-01-15 — "), out)

        # Invalid date format
        out = call(d, "org_log_append", {"entry": "x", "date": "yesterday"})
        assertion("log_append rejects bad date format",
                  "<rpc-error" in out or "Error" in out, out)

        # Empty entry
        out = call(d, "org_log_append", {"entry": "   "})
        assertion("log_append rejects empty entry", "Error: entry is empty" in out, out)

        # Multiline collapse
        out = call(d, "org_log_append", {"entry": "line1\nline2\nline3"})
        parsed = json.loads(out)
        assertion("log_append collapses newlines",
                  "\n" not in parsed["line"] and "line1 line2 line3" in parsed["line"], out)

        # Verify file actually written
        log_path = Path(d) / "log.md"
        assertion("log.md exists after appends", log_path.exists())
        content = log_path.read_text()
        assertion("log.md contains backdated entry", "2025-01-15 — backdated" in content)
    finally:
        teardown_tmpdir(d)


def test_org_save_source():
    d = setup_tmpdir()
    try:
        # Text content
        out = call(d, "org_save_source", {"filename": "Test File.txt", "content": "hello"})
        parsed = json.loads(out)
        assertion("save_source text ok", parsed.get("ok") is True, out)
        assertion("save_source canonicalizes filename",
                  parsed["path"] == "sources/test-file.txt", out)

        # Refuses overwrite (immutable invariant)
        out = call(d, "org_save_source", {"filename": "Test File.txt", "content": "different"})
        assertion("save_source refuses overwrite", "already exists" in out, out)

        # Binary content (PNG header)
        out = call(d, "org_save_source",
                   {"filename": "binary.png", "content_base64": "iVBORw=="})
        parsed = json.loads(out)
        assertion("save_source binary ok", parsed.get("ok") is True, out)
        bin_path = Path(d) / "sources" / "binary.png"
        assertion("save_source binary file written", bin_path.exists() and bin_path.stat().st_size == 4)

        # Both content and content_base64 → reject
        out = call(d, "org_save_source",
                   {"filename": "ambiguous.txt", "content": "x", "content_base64": "eA=="})
        assertion("save_source rejects both content + base64",
                  "<rpc-error" in out or "exactly one" in out, out)

        # Path traversal in filename
        out = call(d, "org_save_source",
                   {"filename": "../../etc/evil.txt", "content": "pwned"})
        assertion("save_source rejects ../ in filename",
                  'must be a plain basename' in out, out)

        # Slash in filename
        out = call(d, "org_save_source", {"filename": "a/b.txt", "content": "x"})
        assertion("save_source rejects / in filename",
                  'must be a plain basename' in out, out)

        # Empty filename
        out = call(d, "org_save_source", {"filename": "", "content": "x"})
        assertion("save_source rejects empty filename",
                  "<rpc-error" in out or "Error" in out, out)

        # Unicode filename (test handles diacritics + non-ascii)
        out = call(d, "org_save_source", {"filename": "café-naïve.txt", "content": "x"})
        parsed = json.loads(out)
        assertion("save_source canonicalizes unicode",
                  parsed.get("ok") is True and "caf" in parsed["path"], out)

        # Confirm no file leaked outside data dir
        repo_etc = REPO_ROOT.parent / "etc"
        assertion("no file leaked outside dataDir",
                  not repo_etc.exists() or "evil.txt" not in [f.name for f in repo_etc.iterdir() if f.is_file()])
    finally:
        teardown_tmpdir(d)


def test_org_write_node():
    d = setup_tmpdir()
    try:
        # Create
        out = call(d, "org_write_node", {
            "path": "nodes/units/test.md",
            "frontmatter": {"id": "test", "type": "unit", "level": "area"},
            "body": "# Test\n\nbody",
            "mode": "create",
        })
        parsed = json.loads(out)
        assertion("write_node create ok", parsed.get("ok") is True, out)
        assertion("write_node action=created", parsed.get("action") == "created", out)

        # Create on existing → fail
        out = call(d, "org_write_node", {
            "path": "nodes/units/test.md",
            "frontmatter": {"id": "test", "type": "unit"},
            "body": "x",
            "mode": "create",
        })
        assertion("write_node create on existing fails",
                  "Error: file exists" in out, out)

        # Update on non-existing → fail
        out = call(d, "org_write_node", {
            "path": "nodes/units/nope.md",
            "frontmatter": {"id": "nope", "type": "unit"},
            "body": "x",
            "mode": "update",
        })
        assertion("write_node update on non-existing fails",
                  "Error: file does not exist" in out, out)

        # Upsert on existing → updated
        out = call(d, "org_write_node", {
            "path": "nodes/units/test.md",
            "frontmatter": {"id": "test", "type": "unit", "level": "area"},
            "body": "second version",
            "mode": "upsert",
        })
        parsed = json.loads(out)
        assertion("write_node upsert existing → updated", parsed.get("action") == "updated", out)
        body_check = (Path(d) / "nodes/units/test.md").read_text()
        assertion("write_node body actually updated", "second version" in body_check)

        # Identity refused without force
        out = call(d, "org_write_node", {
            "path": "identity/m.md",
            "frontmatter": {"id": "m", "type": "identity"},
            "body": "x",
        })
        assertion("write_node identity refused without force",
                  "force_identity" in out, out)

        # Identity allowed with force
        out = call(d, "org_write_node", {
            "path": "identity/m.md",
            "frontmatter": {"id": "m", "type": "identity"},
            "body": "x",
            "force_identity": True,
            "mode": "create",
        })
        parsed = json.loads(out)
        assertion("write_node identity with force=true ok", parsed.get("ok") is True, out)

        # Sources refused (immutable)
        out = call(d, "org_write_node", {
            "path": "sources/anything.md",
            "frontmatter": {"id": "anything", "type": "unit"},
            "body": "x",
        })
        assertion("write_node sources/ refused",
                  "writes restricted" in out or "immutable" in out.lower(), out)

        # log.md refused (use org_log_append)
        out = call(d, "org_write_node", {
            "path": "log.md",
            "frontmatter": {"id": "log", "type": "unit"},
            "body": "x",
        })
        assertion("write_node log.md refused", "writes restricted" in out, out)

        # ID mismatch
        out = call(d, "org_write_node", {
            "path": "nodes/units/foo.md",
            "frontmatter": {"id": "bar", "type": "unit"},
            "body": "x",
        })
        assertion("write_node id mismatch fails",
                  "must match filename slug" in out, out)

        # Missing required frontmatter
        out = call(d, "org_write_node", {
            "path": "nodes/units/x.md",
            "frontmatter": {},
            "body": "x",
        })
        assertion("write_node missing id fails", "must include `id`" in out, out)

        # Path traversal attack
        out = call(d, "org_write_node", {
            "path": "nodes/units/../../../tmp/escape.md",
            "frontmatter": {"id": "escape", "type": "unit"},
            "body": "pwned",
            "mode": "create",
        })
        assertion("write_node path traversal blocked",
                  "Path traversal rejected" in out, out)
        # And verify no file leaked
        assertion("no escape.md outside dataDir",
                  not Path("/tmp/escape.md").exists() and
                  not (Path(d).parent / "tmp" / "escape.md").exists())

        # Non-md extension
        out = call(d, "org_write_node", {
            "path": "nodes/units/test.txt",
            "frontmatter": {"id": "test", "type": "unit"},
            "body": "x",
        })
        assertion("write_node non-md path fails",
                  "must end with .md" in out, out)
    finally:
        teardown_tmpdir(d)


def test_org_read_search_list_neighbors():
    """Use the bundled fixture (mcp-server/test-fixtures/sample-org/) for read-side tests.

    The fixture is a tiny generic Acme example: 1 identity, 2 units, 1 person,
    1 stakeholder, 1 commitment, 1 source. Just enough to verify each tool's
    behaviour without coupling tests to any specific real organization.
    """
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org"
    d = str(fixture)

    # ---- org_read ----
    out = call(d, "org_read", {"id": "operations"})
    assertion("read by bare id finds operations",
              '"id": "operations"' in out, out[:200])

    out = call(d, "org_read", {"id": "nodes/units/operations.md"})
    assertion("read by relative path",
              '"path": "nodes/units/operations.md"' in out, out[:200])

    out = call(d, "org_read", {"id": "nonexistent-node-xyz"})
    assertion("read missing returns helpful error",
              "Node not found" in out, out)

    out = call(d, "org_read", {"id": "../../etc/passwd"})
    assertion("read path traversal blocked",
              "Node not found" in out, out)

    # Root-level Org docs are readable as bare ids
    for doc_id in ("log", "index"):
        out = call(d, "org_read", {"id": doc_id})
        assertion(f"read root doc {doc_id}.md",
                  f'"path": "{doc_id}.md"' in out, out[:200])

    # ---- org_search ----
    out = call(d, "org_search", {"query": "Acme"})
    parsed = json.loads(out)
    assertion("search 'Acme' returns hits",
              parsed.get("total", 0) > 0, out[:200])

    out = call(d, "org_search", {"query": "asdfqwertyzzzz"})
    parsed = json.loads(out)
    assertion("search no-match returns 0 hits",
              parsed.get("total", -1) == 0, out[:200])

    out = call(d, "org_search", {"query": "Acme", "type": "commitment"})
    parsed = json.loads(out)
    types = {h["type"] for h in parsed.get("hits", [])}
    assertion("search type filter applied",
              types == {"commitment"} or len(types) == 0, f"types: {types}")

    out = call(d, "org_search", {"query": "a"})
    assertion("search too-short query rejected",
              "Query too short" in out, out)

    # ---- org_list ----
    out = call(d, "org_list", {"type": "unit"})
    parsed = json.loads(out)
    assertion("list units returns 2",
              parsed.get("total") == 2,
              f"got total={parsed.get('total')}")

    out = call(d, "org_list", {"type": "commitment"})
    parsed = json.loads(out)
    assertion("list commitment returns 1",
              parsed.get("total") == 1,
              f"got total={parsed.get('total')}")

    out = call(d, "org_list", {"path": "nodes/people"})
    parsed = json.loads(out)
    assertion("list path=nodes/people returns 1",
              parsed.get("total") == 1,
              f"got total={parsed.get('total')}")

    out = call(d, "org_list", {"type": "nonexistent-type"})
    parsed = json.loads(out)
    assertion("list invalid type → 0",
              parsed.get("total") == 0, out[:200])

    # ---- org_neighbors ----
    out = call(d, "org_neighbors", {"id": "operations", "depth": 1})
    parsed = json.loads(out)
    assertion("neighbors operations has at least one neighbor",
              len(parsed.get("neighbors", [])) > 0, out[:200])

    out = call(d, "org_neighbors", {"id": "nonexistent"})
    assertion("neighbors missing returns helpful error",
              "Node not found" in out, out)

    out = call(d, "org_neighbors", {"id": "operations", "depth": 4})
    assertion("neighbors depth>3 rejected",
              "<rpc-error" in out or "Error" in out, out[:100])



def test_repo_root_tooling():
    """Tools that resolve via dirname(dataDir) need dataDir to be a direct
    child of the repo root. Use the empty Org/ starter for those.
    """
    real_org = REPO_ROOT / "Org"
    d = str(real_org)

    # ---- org_skills_list ----
    out = call(d, "org_skills_list", {})
    parsed = json.loads(out)
    names = {s["name"] for s in parsed.get("skills", [])}
    expected = {"init", "ingest", "lint",
                "ai-exposure", "value-map", "reshuffle", "world-model", "new-play"}
    assertion(f"skills_list exposes all 8 skills (got {len(names)})",
              expected.issubset(names),
              f"missing: {expected - names}")

    # ---- org_skill_read (top-level + nested + cross-cuts) ----
    out = call(d, "org_skill_read", {"name": "init"})
    parsed = json.loads(out)
    assertion("skill_read init body present",
              len(parsed.get("body", "")) > 500,
              f"body length: {len(parsed.get('body', ''))}")
    assertion("skill_read init path is correct",
              parsed.get("path") == "skills/init/SKILL.md",
              parsed.get("path"))

    out = call(d, "org_skill_read", {"name": "world-model"})
    parsed = json.loads(out)
    assertion("skill_read world-model body present",
              "capabilities" in parsed.get("body", "").lower(),
              parsed.get("path"))
    assertion("skill_read world-model path is correct",
              parsed.get("path") == "skills/playbooks/world-model/SKILL.md",
              parsed.get("path"))

    out = call(d, "org_skill_read", {"name": "STYLE"})
    parsed = json.loads(out)
    assertion("skill_read top-level cross-cut STYLE.md works",
              parsed.get("path") == "skills/STYLE.md",
              parsed.get("path"))

    out = call(d, "org_skill_read", {"name": "nonexistent-skill-xyz"})
    assertion("skill_read missing returns helpful error",
              "Skill not found" in out, out[:200])

    # ---- org_lint_run (Tier 1 only — fast on the empty starter) ----
    out = call(d, "org_lint_run", {"tier": "tier1"})
    parsed = json.loads(out)
    assertion("lint_run tier1 exit_code is 0",
              parsed.get("tier1", {}).get("exit_code") == 0,
              parsed.get("tier1", {}).get("stderr", "")[:200])

    # ---- org_open ----
    out = call(d, "org_open", {"path": "Org/log.md"})
    parsed = json.loads(out)
    assertion("org_open ok on existing file",
              parsed.get("ok") is True, out[:200])
    assertion("org_open returns file_url",
              parsed.get("file_url", "").startswith("file:///"),
              parsed.get("file_url"))

    out = call(d, "org_open", {"path": "../../../etc/passwd"})
    assertion("org_open path traversal blocked",
              "escapes the repo root" in out or "does not exist" in out,
              out[:200])

    out = call(d, "org_open", {"path": "Org/nonexistent-file-xyz.md"})
    assertion("org_open missing file errors cleanly",
              "does not exist" in out, out[:200])

    # org_neighbors depth=4 (over max)
    out = call(d, "org_neighbors", {"id": "personale", "depth": 4})
    assertion("neighbors depth>3 rejected", "<rpc-error" in out or "Error" in out, out[:100])


def test_concurrent_safety():
    """Multiple writes in quick succession must all succeed without corruption."""
    d = setup_tmpdir()
    try:
        # Sequential rapid writes (we don't actually run parallel in stdio — server is single-process)
        for i in range(20):
            out = call(d, "org_log_append", {"entry": f"rapid entry {i}"})
            parsed = json.loads(out)
            if not parsed.get("ok"):
                assertion(f"rapid write {i}", False, out)
                break
        else:
            assertion("20 rapid log appends ok", True)
            log = (Path(d) / "log.md").read_text()
            assertion("all 20 entries present in log",
                      all(f"rapid entry {i}" in log for i in range(20)))
    finally:
        teardown_tmpdir(d)


def test_unicode_payload():
    d = setup_tmpdir()
    try:
        # Unicode in body
        out = call(d, "org_write_node", {
            "path": "nodes/units/unicode.md",
            "frontmatter": {"id": "unicode", "type": "unit", "description": "àèìòù — €"},
            "body": "Cità di Cremona — café — naïve — 你好",
            "mode": "create",
        })
        parsed = json.loads(out)
        assertion("write_node unicode body ok", parsed.get("ok") is True, out)
        content = (Path(d) / "nodes/units/unicode.md").read_text()
        assertion("unicode preserved", "你好" in content and "naïve" in content)

        # Unicode in log (em dash, accented chars, currency)
        out = call(d, "org_log_append", {"entry": "ingest — annual report — €36.7M"})
        parsed = json.loads(out)
        assertion("log_append unicode ok", parsed.get("ok") is True)
    finally:
        teardown_tmpdir(d)


def test_large_payload():
    d = setup_tmpdir()
    try:
        big_body = "Lorem ipsum dolor sit amet. " * 5000  # ~135KB
        out = call(d, "org_write_node", {
            "path": "nodes/units/big.md",
            "frontmatter": {"id": "big", "type": "unit"},
            "body": big_body,
            "mode": "create",
        })
        parsed = json.loads(out)
        assertion("write_node large body ok", parsed.get("ok") is True, out[:200])
        size = (Path(d) / "nodes/units/big.md").stat().st_size
        assertion("large file written approximately right size", size > 100_000)
    finally:
        teardown_tmpdir(d)


# ============================================================================
# Run all
# ============================================================================

def main():
    if not SERVER.exists():
        print(f"FAIL: server not built at {SERVER}", file=sys.stderr)
        sys.exit(2)

    run_section("Tool listing", test_tools_listing)
    run_section("org_log_append", test_org_log_append)
    run_section("org_save_source", test_org_save_source)
    run_section("org_write_node", test_org_write_node)
    run_section("Read-side tools (read/search/list/neighbors)", test_org_read_search_list_neighbors)
    run_section("Repo-root tooling (skills_list, skill_read, lint_run, open)", test_repo_root_tooling)
    run_section("Concurrent safety", test_concurrent_safety)
    run_section("Unicode payloads", test_unicode_payload)
    run_section("Large payloads", test_large_payload)

    print(f"\n{'='*60}")
    print(f"PASS: {passes}")
    print(f"FAIL: {len(failures)}")
    for label, detail in failures:
        print(f"  FAIL  {label}")
        if detail:
            print(f"        {detail[:200]}")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
