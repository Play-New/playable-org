#!/usr/bin/env python3
"""
End-to-end test harness for the mcp-server.

Spawns the server via stdio for each test, sends a JSON-RPC request,
asserts on the response. Exits non-zero on any failure.

Run: python3 test-e2e.py
"""

import json
import os
import re
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


def _test_env() -> dict[str, str]:
    """Subprocess env with PLAYABLE_ORG_TEST_MODE=1 so org_open doesn't
    spawn the OS file-open handler during tests (was causing log.md to
    pop up in the editor on every test run)."""
    env = os.environ.copy()
    env["PLAYABLE_ORG_TEST_MODE"] = "1"
    return env


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
        env=_test_env(),
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
        env=_test_env(),
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
        assertion("13 tools registered", len(names) == 13, f"got {len(names)}: {names}")
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

    The fixture is the Outline & Co. fake studio: 5 units, 14 activities,
    5 people, 4 stakeholders, 4 commitments. Rich enough to exercise the
    read-side mcp tools against realistic graph structure.
    """
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org"
    d = str(fixture)

    # ---- org_read ----
    out = call(d, "org_read", {"id": "strategy"})
    assertion("read by bare id finds strategy",
              '"id": "strategy"' in out, out[:200])

    out = call(d, "org_read", {"id": "nodes/units/strategy.md"})
    assertion("read by relative path",
              '"path": "nodes/units/strategy.md"' in out, out[:200])

    out = call(d, "org_read", {"id": "nonexistent-node-xyz"})
    assertion("read missing returns helpful error",
              "Node not found" in out, out)

    out = call(d, "org_read", {"id": "../../etc/passwd"})
    assertion("read path traversal blocked",
              "Node not found" in out, out)

    # Root-level org docs are readable as bare ids
    for doc_id in ("log", "index"):
        out = call(d, "org_read", {"id": doc_id})
        assertion(f"read root doc {doc_id}.md",
                  f'"path": "{doc_id}.md"' in out, out[:200])

    # ---- org_search ----
    out = call(d, "org_search", {"query": "Outline"})
    parsed = json.loads(out)
    assertion("search 'Outline' returns hits",
              parsed.get("total", 0) > 0, out[:200])

    out = call(d, "org_search", {"query": "asdfqwertyzzzz"})
    parsed = json.loads(out)
    assertion("search no-match returns 0 hits",
              parsed.get("total", -1) == 0, out[:200])

    out = call(d, "org_search", {"query": "Outline", "type": "commitment"})
    parsed = json.loads(out)
    types = {h["type"] for h in parsed.get("hits", [])}
    assertion("search type filter applied",
              types == {"commitment"} or len(types) == 0, f"types: {types}")

    out = call(d, "org_search", {"query": "a"})
    assertion("search too-short query rejected",
              "Query too short" in out, out)

    # ---- org_list ----
    # Counts match the Outline & Co. fixture (5 units, 4 commitments,
    # 5 people, 14 activities, 4 stakeholders).
    out = call(d, "org_list", {"type": "unit"})
    parsed = json.loads(out)
    assertion("list units returns 5",
              parsed.get("total") == 5,
              f"got total={parsed.get('total')}")

    out = call(d, "org_list", {"type": "commitment"})
    parsed = json.loads(out)
    assertion("list commitment returns 4",
              parsed.get("total") == 4,
              f"got total={parsed.get('total')}")

    out = call(d, "org_list", {"path": "nodes/people"})
    parsed = json.loads(out)
    assertion("list path=nodes/people returns 5",
              parsed.get("total") == 5,
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

    # ---- org_play_run (graph build) ----
    # Graph build mechanically walks the structure — no AEI input needed.
    # Asserts the build returns nodes + edges + a topology summary.
    # Use a fixed out_name so the test cleans up after itself instead of
    # leaking a date-stamped artefact into the fixture every run.
    test_artefact = "graph-e2e-test-fixture"
    test_artefact_path = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / f"{test_artefact}.json"
    try:
        out = call(d, "org_play_run", {
            "playbook": "graph",
            "mode": "build",
            "out_name": test_artefact,
        })
        parsed = json.loads(out)
        assertion("play_run graph build status ok",
                  parsed.get("status") == "ok",
                  f"status={parsed.get('status')}, stderr={parsed.get('stderr', '')[:200]}")
        skel = parsed.get("skeleton") or {}
        assertion("play_run graph build returns nodes",
                  len(skel.get("nodes", [])) >= 30,
                  f"nodes count: {len(skel.get('nodes', []))}")
        assertion("play_run graph build returns edges",
                  len(skel.get("edges", [])) >= 100,
                  f"edges count: {len(skel.get('edges', []))}")
        assertion("play_run graph build returns topology summary",
                  "_topology" in skel and "by_node_kind" in skel["_topology"],
                  str(skel.get("_topology", {}))[:200])
        # Defect-to-test: build.py must emit `_org` (read from
        # identity/mission.md frontmatter `org_name` key) so the
        # viewer's dateline doesn't fall through to a generic
        # placeholder when invoked via the mcp pipeline that doesn't
        # pass --org-name.
        assertion("play_run graph build returns _org",
                  isinstance(skel.get("_org"), str) and skel["_org"],
                  f"_org={skel.get('_org')!r}")
        assertion("play_run graph build _org matches sample-org identity",
                  skel.get("_org") == "Outline & Co.",
                  f"_org={skel.get('_org')!r}")
    finally:
        if test_artefact_path.exists():
            test_artefact_path.unlink()

    # ---- org_autoresearch_run — was untested in the suite (caught during
    # the May 2026 sweep). Defect-to-test for two real bugs found:
    # the tool's `inferPlaybook` filename helper missed `graph-*`, and
    # the playbook enum excluded `graph` entirely. Both fixed; this test
    # locks the fix.
    sample_play = "plays/data/graph-outline-2026-05-09.json"  # relative to sample-org dataDir
    out = call(d, "org_autoresearch_run", {"play_path": sample_play})
    try:
        parsed = json.loads(out)
    except json.JSONDecodeError:
        parsed = {}
    overall = parsed.get("overall") if isinstance(parsed, dict) else None
    assertion("autoresearch_run on graph play returns PASS",
              overall == "PASS",
              f"overall={overall}, body={out[:200]}")
    assertion("autoresearch_run reports the four deterministic dimensions",
              isinstance(parsed, dict) and len(parsed.get("dimensions", [])) >= 4,
              str(parsed.get("dimensions", []) if isinstance(parsed, dict) else parsed)[:200])
    assertion("autoresearch_run accepts 'graph' as a playbook (no inference error)",
              "could not infer playbook" not in out,
              out[:200])



def test_graph_viewer_design_regression():
    """Regression net for the graph viewer's HTML output. Locks in the
    decisions we converged to: App-pure layout, paper palette
    (Carta sbiadita v2), Pointer Events + pinch zoom, safe-area-inset,
    inline favicon, embedded Inter Variable font, focus permalink,
    grouped inspect panel by verb. Body-markdown link edges and corpus /
    declarative kinds are stripped from the viewer (see SKILL.md).

    Runs viewer.py directly against the canonical sample-org fixture
    JSON. Defect-to-test principle: every issue we fixed in the design
    iteration is now an automated check.
    """
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "graph-outline-2026-05-09.json"
    viewer = REPO_ROOT / "skills" / "playbooks" / "graph" / "viewer.py"
    out_html = Path(tempfile.mkdtemp(prefix="graph-viewer-test-")) / "out.html"
    try:
        proc = subprocess.run(
            ["python3", str(viewer),
             "--map", str(fixture),
             "--html", str(out_html),
             "--title", "test",
             "--org-name", "test"],
            capture_output=True, text=True, timeout=15,
        )
        assertion("graph viewer renders without error",
                  proc.returncode == 0,
                  f"stderr={proc.stderr[:300]}")
        html = out_html.read_text()

        # ---- structural shell (App-pure layout) ----
        assertion("viewer has full-bleed canvas tag",
                  '<canvas id="canvas">' in html)
        assertion("viewer has top-right Analysis button",
                  'id="open-analysis"' in html and 'class="analysis"' in html)
        assertion("viewer has floating inspect panel",
                  'class="inspect"' in html and 'id="inspect"' in html)
        assertion("viewer has analysis modal",
                  'class="modal-scrim"' in html and 'id="modal-scrim"' in html)
        assertion("viewer has bottom-center hint",
                  'class="hint"' in html and 'id="hint"' in html)
        assertion("viewer has bottom kinds ribbon",
                  'class="kinds"' in html and 'id="kinds"' in html)

        # ---- inspect grouping by verb (was the "involved in × 13" bug) ----
        assertion("inspect groups rels by verb",
                  'rel-verb' in html and 'rel-verb-count' in html)

        # ---- mobile-app polish ----
        assertion("safe-area-inset honoured",
                  'env(safe-area-inset-' in html)
        assertion("touch-action: none on canvas",
                  'touch-action: none' in html)
        assertion("pinch-zoom handler present",
                  'pointers.size === 2' in html and "'pointerdown'" in html)
        assertion("apple-mobile-web-app capable meta",
                  'apple-mobile-web-app-capable' in html)
        assertion("viewport-fit=cover for iPhone notch",
                  'viewport-fit=cover' in html)
        assertion("theme-color set for browser chrome",
                  'name="theme-color"' in html)

        # ---- favicon (inline, no extra file) ----
        assertion("inline SVG favicon",
                  'rel="icon"' in html and 'data:image/svg+xml' in html)

        # ---- font embedded (no CDN, file:// works) ----
        assertion("Inter Variable embedded as data URL",
                  'data:font/woff2;base64,' in html)
        assertion("Inter ss01 + cv11 features active",
                  '"ss01"' in html and '"cv11"' in html)

        # ---- Carta sbiadita v2 palette ----
        assertion("unit colour is slate (Carta sbiadita)",
                  '#6b7d8c' in html)
        assertion("activity colour is sage",
                  '#8a9d6b' in html)
        assertion("commitment colour is terracotta",
                  '#b87b5e' in html)

        # ---- focus permalink ----
        assertion("?focus=<id> permalink handler wired",
                  "params.get('focus')" in html or 'params.get("focus")' in html)

        # ---- viewer scope: operational dependencies only ----
        assertion("viewer drops corpus/declarative kinds (no source pill)",
                  '"id":"source"' not in html and '"id": "source"' not in html)
        assertion("viewer drops corpus/declarative kinds (no identity pill)",
                  '"id":"identity"' not in html and '"id": "identity"' not in html)
        assertion("viewer drops corpus/declarative kinds (no language pill)",
                  '"id":"language-term"' not in html and '"id": "language-term"' not in html)
        assertion("viewer drops corpus/declarative kinds (no financial pill)",
                  '"id":"financial-summary"' not in html and '"id": "financial-summary"' not in html)
        assertion("viewer drops link edges (markdown cross-references aren't dependencies)",
                  '"verb":"link"' not in html and '"verb": "link"' not in html)
        assertion("viewer drops cite edges (sources aren't in the graph)",
                  '"verb":"cite"' not in html and '"verb": "cite"' not in html)

        # ---- no orphan Python format placeholders ----
        # JS template literals look like ${x} which is fine; we only
        # care about Python-style {x} that .format() should have filled.
        import re
        unfilled = re.findall(r'(?<!\$)\{[a-z_][a-z0-9_]*\}', html)
        assertion("no orphan Python format placeholders in output",
                  len(unfilled) == 0,
                  f"found: {unfilled[:5]}")
    finally:
        shutil.rmtree(out_html.parent, ignore_errors=True)


def _render_viewer_to_tmp(playbook: str, fixture: Path, *, mode: str = "map") -> str:
    """Run a playbook viewer against the canonical fixture and return the HTML.
    mode = 'map' for --map/--html, 'matches' for --matches/--out (ai-exposure),
    'mapsvg' for --map/--html/--svg (value-map). Raises on non-zero exit."""
    viewer = REPO_ROOT / "skills" / "playbooks" / playbook / "viewer.py"
    tmp = Path(tempfile.mkdtemp(prefix=f"{playbook}-viewer-test-"))
    out_html = tmp / "out.html"
    try:
        if mode == "matches":
            args = ["python3", str(viewer), "--matches", str(fixture), "--out", str(out_html)]
        elif mode == "mapsvg":
            args = ["python3", str(viewer), "--map", str(fixture), "--html", str(out_html), "--svg", str(tmp / "out.svg")]
        else:
            args = ["python3", str(viewer), "--map", str(fixture), "--html", str(out_html)]
        proc = subprocess.run(args, capture_output=True, text=True, timeout=20)
        assertion(f"{playbook} viewer renders without error",
                  proc.returncode == 0,
                  f"stderr={proc.stderr[:300]}")
        return out_html.read_text()
    finally:
        # Caller may want to inspect tmp; but for these tests we read text
        # and discard the tmp dir.
        shutil.rmtree(tmp, ignore_errors=True)


def _assert_no_jargon_in_user_visible(playbook: str, html: str):
    """Strip <script>, <style>, <!-- ... --> and assert that user-visible
    prose has none of the framework jargon banned by skills/STYLE.md.

    Acronyms (DRI, IC, SLO) — never visible.
    Forbidden words in body prose (moat, commodity, commoditize, etc.) — never visible.
    The visual code labels 'differentiated' and 'standard' replace 'moat' and 'commodity'.
    """
    import re
    s = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.S)
    s = re.sub(r'<style[^>]*>.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<!--.*?-->', '', s, flags=re.S)
    patterns = [
        (r'\bDRI\b', 'DRI acronym'),
        (r'\bIC[s]?\b', 'IC acronym'),
        (r'\bSLO\b', 'SLO acronym'),
        (r'\bmoat\b', '"moat" in body prose (use "differentiated")'),
        (r'\bcommodity\b', '"commodity" in body prose (use "standard")'),
        (r'engine candidate', '"engine candidate" jargon'),
        (r'coordination tax', '"coordination tax" jargon'),
        (r'judgment density', '"judgment density" jargon'),
        (r'capability stack', '"capability stack" jargon'),
        (r'failure[ -]signal', '"failure signal" jargon'),
        (r'piece-to-build', 'kebab "piece-to-build" leaking into prose'),
        (r'commoditiz', '"commoditize" jargon'),
    ]
    for pat, desc in patterns:
        m = re.search(pat, s)
        assertion(f"{playbook}: no {desc} in user-visible prose",
                  m is None,
                  f"found near: ...{s[max(0,m.start()-40):m.end()+40] if m else ''}...")


def test_ai_exposure_viewer_design_regression():
    """Regression net for ai-exposure viewer. Locks in:
    App-pure scroll-on-paper shell with ? + Analysis chrome, unit filter
    pills, activity grid, per-activity popover showing AEI matches table,
    decisions in Analysis modal. No jargon leak in user prose (per STYLE.md)."""
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "ai-exposure-outline-2026-05-07.json"
    html = _render_viewer_to_tmp("ai-exposure", fixture, mode="matches")

    # Shell + chrome
    assertion("ai-exposure: editorial column container present",
              'class="wrap"' in html or 'editorial' in html or 'max-width' in html)
    assertion("ai-exposure: ? help button + about modal scaffold",
              'id="open-help"' in html and 'id="about-scrim"' in html)
    assertion("ai-exposure: Analysis CTA + modal scaffold",
              'id="open-analysis"' in html and 'id="modal-scrim"' in html)
    assertion("ai-exposure: theme-color meta",
              'name="theme-color"' in html)
    assertion("ai-exposure: inline SVG favicon (no external assets)",
              'rel="icon"' in html and 'data:image/svg+xml' in html)
    assertion("ai-exposure: Inter Variable embedded",
              'data:font/woff2;base64,' in html)

    # AEI-specific content
    assertion("ai-exposure: unit filter pills",
              'data-unit' in html)
    assertion("ai-exposure: activity cards present",
              'class="card' in html)

    _assert_no_jargon_in_user_visible("ai-exposure", html)

    # No orphan format placeholders. The viewer ships a runtime i18n
    # dictionary (JS uses .replace('{n}', value) at render-time) so we
    # whitelist those known tokens before checking.
    import re
    I18N_TOKENS = {'{n}', '{total}', '{x}'}
    unfilled = [u for u in re.findall(r'(?<!\$)\{[a-z_][a-z0-9_]*\}', html) if u not in I18N_TOKENS]
    assertion("ai-exposure: no orphan Python format placeholders",
              len(unfilled) == 0, f"found: {unfilled[:5]}")


def test_value_map_viewer_design_regression():
    """Regression net for value-map viewer. Locks in:
    SVG map on a 4-stage evolution axis, framework axis labels (Genesis /
    Custom / Product / Commodity allowed AS axis labels per STYLE.md),
    component cards, coral border for emerging components, no commodity /
    commoditize in body prose, ? + Analysis chrome."""
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "value-map-studio-mid-market-baseline-2026-05-07.json"
    html = _render_viewer_to_tmp("value-map", fixture, mode="mapsvg")

    # Shell + chrome
    assertion("value-map: ? help button + about modal scaffold",
              'id="open-help"' in html and 'id="about-scrim"' in html)
    assertion("value-map: Analysis CTA + modal scaffold",
              'id="open-analysis"' in html and 'id="modal-scrim"' in html)
    assertion("value-map: Inter Variable embedded",
              'data:font/woff2;base64,' in html)
    assertion("value-map: inline SVG favicon",
              'rel="icon"' in html and 'data:image/svg+xml' in html)
    assertion("value-map: theme-color meta",
              'name="theme-color"' in html)

    # Map-specific content
    assertion("value-map: SVG map element present",
              '<svg' in html and 'viewBox' in html)
    assertion("value-map: 4-stage evolution axis labelled",
              'Genesis' in html and 'Custom' in html and 'Product' in html and 'Commodity' in html)

    # Anti-rhetoric: 'commoditize' must not appear, 'commodity' only as
    # axis label (we just asserted Commodity capitalized as the axis stop;
    # any lowercase 'commodity' in body prose is a leak).
    _assert_no_jargon_in_user_visible("value-map", html)

    import re
    unfilled = re.findall(r'(?<!\$)\{[a-z_][a-z0-9_]*\}', html)
    assertion("value-map: no orphan Python format placeholders",
              len(unfilled) == 0, f"found: {unfilled[:5]}")


def test_reshuffle_viewer_design_regression():
    """Regression net for reshuffle viewer. Locks in:
    Canvas-first 3x3 matrix (AI class × constraint), 'where AI changes
    structure' highlight on the leverage cell, activity chips clickable,
    direction options inside Analysis modal, ? + Analysis chrome, no
    'engine candidate' jargon in user prose."""
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "reshuffle-outline-2026-05-07.json"
    html = _render_viewer_to_tmp("reshuffle", fixture)

    # Shell + chrome
    assertion("reshuffle: ? help button + about modal scaffold",
              'id="open-help"' in html and 'id="about-scrim"' in html)
    assertion("reshuffle: Analysis CTA + modal scaffold",
              'id="open-analysis"' in html and 'id="modal-scrim"' in html)
    assertion("reshuffle: Inter Variable embedded",
              'data:font/woff2;base64,' in html)
    assertion("reshuffle: inline SVG favicon",
              'rel="icon"' in html and 'data:image/svg+xml' in html)
    assertion("reshuffle: theme-color meta",
              'name="theme-color"' in html)

    # Matrix-specific content
    assertion("reshuffle: 3x3 matrix container present",
              'class="matrix"' in html)
    assertion("reshuffle: matrix has the three AI-class rows",
              'AI as infrastructure' in html and 'AI as accelerator' in html and 'AI not relevant' in html)
    assertion("reshuffle: leverage cell badge 'where AI changes structure'",
              'where AI changes structure' in html)

    _assert_no_jargon_in_user_visible("reshuffle", html)

    import re
    unfilled = re.findall(r'(?<!\$)\{[a-z_][a-z0-9_]*\}', html)
    assertion("reshuffle: no orphan Python format placeholders",
              len(unfilled) == 0, f"found: {unfilled[:5]}")


def test_world_model_viewer_design_regression():
    """Regression net for world-model viewer. Locks in:
    Editorial column 820px inside 1240px, three layers (Interfaces top,
    Capabilities middle dominant, World models bottom 2-column), middle-
    layer annotation between Capabilities and World models, capability
    cards with sentence-cased names + 'callable N/5' dots, ? + Analysis
    chrome, Analysis modal has 'The move, in three steps' + decisions,
    no missing-capabilities section on the page or in the modal."""
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "world-model-outline-2026-05-07.json"
    html = _render_viewer_to_tmp("world-model", fixture)

    # Shell + chrome
    assertion("world-model: ? help button + about modal scaffold",
              'id="open-help"' in html and 'id="about-scrim"' in html)
    assertion("world-model: Analysis CTA + modal scaffold",
              'id="open-analysis"' in html and 'id="modal-scrim"' in html)
    assertion("world-model: editorial 820px column class present",
              'max-width: 820px' in html or '.editorial' in html or 'wm-body' in html)
    assertion("world-model: Inter Variable embedded",
              'data:font/woff2;base64,' in html)
    assertion("world-model: inline SVG favicon",
              'rel="icon"' in html and 'data:image/svg+xml' in html)
    assertion("world-model: theme-color meta",
              'name="theme-color"' in html)

    # 3-layer stack
    assertion("world-model: Interfaces layer present",
              'data-layer="interfaces"' in html or 'layer-interfaces' in html or '>Interfaces<' in html)
    assertion("world-model: Capabilities layer present",
              'data-layer="capabilities"' in html or 'layer-capabilities' in html or '>Capabilities<' in html)
    assertion("world-model: World models band (plural)",
              '>World models<' in html or '>World model<' in html)
    assertion("world-model: middle-layer annotation between Capabilities and World models",
              'intelligence-annotation' in html)

    # 2-column world model band (organization side + stakeholder side)
    assertion("world-model: 'Organization side' sub-section present",
              'Organization side' in html)
    assertion("world-model: 'Stakeholder side' sub-section present",
              'Stakeholder side' in html)

    # Capability cards: sentence-case names + callable N/5 dots
    assertion("world-model: capability cards rendered",
              'cap-card' in html)
    assertion("world-model: 'callable N/5' wrapper-status label",
              'callable ' in html and '/5' in html)
    assertion("world-model: sentence-cased capability name (no visible kebab)",
              '>Define positioning<' in html or 'Define positioning' in html)
    # Kebab IDs are still in data-id for stable lookup — must NOT appear as visible card name
    assertion("world-model: kebab capability id NOT shown as card title",
              '<h3 class="card-name">define-positioning</h3>' not in html)

    # Coral border for differentiated capabilities, hairline for standard.
    # Visual code is in EXTRA_CSS; we just assert the classes exist on cards.
    assertion("world-model: 'differentiated' class on moat cards",
              'cap-card differentiated' in html)
    assertion("world-model: 'standard' class on commodity cards",
              'cap-card standard' in html)

    # Analysis modal structure: 3 moves + decisions, NO missing-capabilities
    assertion("world-model: Analysis modal has 'The move, in three steps' section",
              'The move, in three steps' in html)
    assertion("world-model: 'Running the loop' headline in Analysis modal",
              'Running the loop' in html)
    # The roadmap section (if rendered) lived under #roadmap or .roadmap-section
    # in the OLD design. In the current shape it must NOT appear as an on-page
    # section. The cards themselves may still exist as dead code in the JS
    # NODES dict for backwards compatibility; what matters is no on-page block.
    import re
    # ensure no <section class="roadmap-section" on page (was the on-page
    # roadmap block we deliberately removed)
    assertion("world-model: no on-page roadmap-section block",
              re.search(r'<section[^>]*class="[^"]*roadmap-section', html) is None)

    # Anti-rhetoric / no jargon
    _assert_no_jargon_in_user_visible("world-model", html)

    # Plain-language labels (replacements for DRI / Callable by / Composes with)
    # appear in the JS, but the popover *content* uses these phrases.
    # Confirm the popover renderer is wired with the plain labels (JS strings
    # are inside <script>, so search the raw html before strip).
    assertion("world-model: popover uses 'Run by' label on card meta",
              'Run by' in html)
    assertion("world-model: popover uses 'Who can ask for it' label",
              "Who can ask for it" in html)
    assertion("world-model: popover uses 'Used together with' label",
              "Used together with" in html)
    assertion("world-model: popover uses 'callable today' framing",
              "How callable today" in html or "callable today" in html.lower())

    # No orphan Python placeholders
    unfilled = re.findall(r'(?<!\$)\{[a-z_][a-z0-9_]*\}', html)
    assertion("world-model: no orphan Python format placeholders",
              len(unfilled) == 0, f"found: {unfilled[:5]}")


def test_value_map_end_user_normalization():
    """`value-map/viewer.py` accepts `end_user` as a string, a list of
    strings, or a single dict {id, label}. A dict naively iterated
    yields the dict's KEYS as labels — on the first AIRC value-map
    render (2026-05-18) the agent passed `{'id': 'c21', 'label':
    'Ricercatori finanziati'}` and the viewer drew two black disks
    labelled 'id' and 'label' at the top of the chain.

    `_normalize_end_users` coerces every accepted shape to a list of
    label strings. This test pins each shape so the bug stays fixed.
    """
    skills_path = REPO_ROOT / "skills" / "playbooks" / "value-map"
    code = (
        "import sys; sys.path.insert(0, %r); from viewer import _normalize_end_users as N;"
        "print(N('a'));"
        "print(N(['a','b']));"
        "print(N({'id': 'c21', 'label': 'Ricercatori finanziati'}));"
        "print(N({'id': 'only-id'}));"
        "print(N([{'label':'x'},{'id':'y'}]));"
        "print(N(None));"
        "print(N(''));"
    ) % str(skills_path)
    proc = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=10)
    assertion("_normalize_end_users script runs", proc.returncode == 0, proc.stderr[:300])
    lines = proc.stdout.strip().splitlines()
    assertion("normalize str -> [{label}]", lines[0] == "[{'label': 'a'}]", lines[0])
    assertion("normalize list[str] -> [{label},...]",
              lines[1] == "[{'label': 'a'}, {'label': 'b'}]", lines[1])
    assertion("normalize dict {id,label} -> [{label}]",
              lines[2] == "[{'label': 'Ricercatori finanziati'}]", lines[2])
    assertion("normalize dict {id only} -> [{label:id}]",
              lines[3] == "[{'label': 'only-id'}]", lines[3])
    assertion("normalize list[dict] -> list[{label}]",
              lines[4] == "[{'label': 'x'}, {'label': 'y'}]", lines[4])
    assertion("normalize None -> []", lines[5] == "[]", lines[5])
    assertion("normalize empty string -> []", lines[6] == "[]", lines[6])


def test_design_inline_md():
    """`design.inline_md(s)` is the single helper every viewer uses to render
    agent-authored prose (decision answers, rebundle narrations, area notes).
    The bug it fixes: viewers used to `html.escape()` the whole paragraph,
    so `**bold**` and `*italic*` written by the agent leaked as literal
    asterisks. The helper escapes first then applies the three inline forms
    (bold, italic, code) on the escaped string, keeping it XSS-safe.

    Defect-to-test: AIRC's first graph play in 2026-05 showed `**Acronimi
    sciolti e zone bianche.**` as literal text in the Analysis modal.
    """
    skills_path = REPO_ROOT / "skills"
    code = (
        "import sys; sys.path.insert(0, %r); from design import inline_md;"
        "print(inline_md(%r));"
        "print(inline_md(%r));"
        "print(inline_md(%r));"
        "print(inline_md(%r));"
        "print(inline_md(%r));"
    ) % (
        str(skills_path),
        "**bold** word",
        "an *italic* word",
        "use `code` here",
        "plain text only",
        "escape <script>",
    )
    proc = subprocess.run(["python3", "-c", code], capture_output=True, text=True, timeout=10)
    assertion("inline_md script runs", proc.returncode == 0, proc.stderr[:300])
    lines = proc.stdout.strip().splitlines()
    assertion("inline_md: **bold** -> <strong>", lines[0] == "<strong>bold</strong> word", lines[0])
    assertion("inline_md: *italic* -> <em>", lines[1] == "an <em>italic</em> word", lines[1])
    assertion("inline_md: `code` -> <code>", lines[2] == "use <code>code</code> here", lines[2])
    assertion("inline_md: plain text passes through", lines[3] == "plain text only", lines[3])
    assertion("inline_md: HTML special chars escaped", lines[4] == "escape &lt;script&gt;", lines[4])


def test_graph_viewer_lang_it():
    """`graph/viewer.py --lang it` swaps the chrome + About modal copy
    into Italian, leaving decisions in whatever language the agent wrote
    them. Default `--lang en` is unchanged (the design-regression test
    above locks the English snapshot).

    Defect-to-test: AIRC's first re-render on 2026-05-15 showed English
    chrome ("Analysis", "Inspect", "Reset focus", "Reading the
    structure", the whole About modal copy) on an Italian foundation.
    """
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "graph-outline-2026-05-09.json"
    viewer = REPO_ROOT / "skills" / "playbooks" / "graph" / "viewer.py"
    out_html = Path(tempfile.mkdtemp(prefix="graph-viewer-lang-it-")) / "out.html"
    try:
        proc = subprocess.run(
            ["python3", str(viewer),
             "--map", str(fixture),
             "--html", str(out_html),
             "--lang", "it",
             "--title", "test",
             "--org-name", "Test Org"],
            capture_output=True, text=True, timeout=15,
        )
        assertion("graph viewer --lang it runs",
                  proc.returncode == 0, proc.stderr[:300])
        html = out_html.read_text()
        # Chrome buttons
        assertion("--lang it: Analysis button reads 'Analisi'",
                  ">Analisi<" in html and ">Analysis<" not in html)
        assertion("--lang it: Inspect eyebrow reads 'Ispeziona'",
                  ">Ispeziona<" in html and ">Inspect<" not in html)
        assertion("--lang it: help button title reads italian",
                  "Cos&#x27;è questa mappa?" in html or "Cos'è questa mappa?" in html)
        # Analysis modal kicker
        assertion("--lang it: Analysis modal kicker is Italian",
                  "Lettura della struttura" in html and "Reading the structure" not in html)
        # About modal body
        assertion("--lang it: about modal lede is Italian",
                  "La struttura operativa come è stata scritta" in html)
        assertion("--lang it: 'Cosa mostra la mappa' h2 present",
                  "Cosa mostra la mappa" in html)
        assertion("--lang it: English About-modal h2 'What this map shows' is gone",
                  "What this map shows" not in html)
    finally:
        shutil.rmtree(out_html.parent, ignore_errors=True)


def test_graph_autoresearch_failure_modes():
    """`autoresearch.py` is the deterministic gate that refuses bad
    decisions. This locks in the five specific failure modes the AIRC
    instance surfaced through five iterations of decision rewrites
    (May 2026). For each, a minimal synthetic JSON triggers exactly
    one dimension to fail; the clean control passes all five.

    Defect-to-test: each failure mode is one a user had to flag by
    hand before; from now on the gate catches them mechanically.
    """
    fixture = REPO_ROOT / "mcp-server" / "test-fixtures" / "sample-org" / "plays" / "data" / "graph-outline-2026-05-09.json"
    autoresearch = REPO_ROOT / "skills" / "playbooks" / "graph" / "autoresearch.py"

    # Load the clean play once; mutate copies of it per case.
    clean = json.loads(fixture.read_text(encoding="utf-8"))

    def run_with(decisions_patch, expect_fail_dim=None):
        """Write a tmp JSON with patched decisions[] and run autoresearch.
        If `expect_fail_dim` is None, expect PASS overall. Otherwise
        expect FAIL with the named dimension failing."""
        patched = dict(clean)
        patched["decisions"] = decisions_patch
        d = Path(tempfile.mkdtemp(prefix="ar-test-"))
        try:
            p = d / "play.json"
            p.write_text(json.dumps(patched, ensure_ascii=False, indent=2))
            proc = subprocess.run(
                ["python3", str(autoresearch), "--map", str(p)],
                capture_output=True, text=True, timeout=15,
            )
            out = proc.stdout + proc.stderr
            return proc.returncode, out
        finally:
            shutil.rmtree(d, ignore_errors=True)

    # Build a baseline good decision triple to mutate, derived from
    # the existing fixture so it already passes recognizability +
    # audit-grounded. Each case below changes ONE thing.
    base = clean["decisions"]

    # --- case 1: em dash in answer triggers plain-language fail ---
    bad_emdash = json.loads(json.dumps(base))
    bad_emdash[0]["answer"] = bad_emdash[0]["answer"] + " — bonus aside."
    rc, out = run_with(bad_emdash, expect_fail_dim="plain language")
    assertion("autoresearch fails on em dash in decision",
              rc != 0 and "plain language" in out and "—" in out)

    # --- case 2: rhetorical formula 'Significa X, non Y' ---
    bad_formula = json.loads(json.dumps(base))
    bad_formula[0]["answer"] = "Significa governance, non lavoro. " + bad_formula[0]["answer"]
    rc, out = run_with(bad_formula, expect_fail_dim="plain language")
    assertion("autoresearch fails on 'Significa X, non Y' formula",
              rc != 0 and "plain language" in out)

    # --- case 3: meta-rhetorical 'il grafo dichiara' ---
    bad_meta = json.loads(json.dumps(base))
    bad_meta[0]["answer"] = "Il grafo dichiara che le aree pesano. " + bad_meta[0]["answer"]
    rc, out = run_with(bad_meta, expect_fail_dim="plain language")
    assertion("autoresearch fails on 'il grafo dichiara' meta-rhetoric",
              rc != 0 and "plain language" in out)

    # --- case 4: Italian graph jargon 'dipendenze documentate' ---
    bad_jargon = json.loads(json.dumps(base))
    bad_jargon[0]["answer"] = "Le aree con più dipendenze documentate. " + bad_jargon[0]["answer"]
    rc, out = run_with(bad_jargon, expect_fail_dim="plain language")
    assertion("autoresearch fails on 'dipendenze documentate' jargon",
              rc != 0 and "plain language" in out)

    # --- case 5: node_id listed but not linked in answer ---
    bad_unlinked = json.loads(json.dumps(base))
    # Pick a node already in node_ids that we can strip the link to.
    target_id = bad_unlinked[0]["node_ids"][0]
    bad_unlinked[0]["answer"] = re.sub(
        rf"\[([^\]]+)\]\({re.escape(target_id)}\)",
        r"\1",  # keep the label, drop the link
        bad_unlinked[0]["answer"],
    )
    rc, out = run_with(bad_unlinked, expect_fail_dim="linked references")
    assertion("autoresearch fails when a node_id is named but not linked",
              rc != 0 and "linked references" in out and target_id in out)

    # --- case 6: clean control passes ---
    rc, out = run_with(base)
    assertion("autoresearch passes on the clean baseline",
              rc == 0 and "AUTORESEARCH PASS" in out,
              out[-300:] if rc != 0 else "")


def test_graph_build_skips_readme_stubs():
    """`graph/build.py` walks every `<subdir>/*.md`. The public template ships
    a folder-doc `README.md` inside each org subfolder (commitments/, financials/,
    language/, sources/, nodes/units/, nodes/people/, nodes/roles/,
    nodes/activities/, nodes/stakeholders/). Those are documentation, not
    nodes. Earlier versions of build.py picked them up as nodes with
    id="README", producing 9 duplicate ids and an audit failure the first
    time a populated fork ran the graph play. The build now filters them.

    Defect-to-test: AIRC migration on 2026-05-15 surfaced this on the very
    first audit.
    """
    real_org = REPO_ROOT / "org"
    build = REPO_ROOT / "skills" / "playbooks" / "graph" / "build.py"
    out_json = Path(tempfile.mkdtemp(prefix="graph-build-readme-")) / "graph.json"
    try:
        proc = subprocess.run(
            ["python3", str(build), "--org-dir", str(real_org), "--out", str(out_json)],
            capture_output=True, text=True, timeout=15,
        )
        assertion("graph build runs on empty template", proc.returncode == 0, proc.stderr[:300])
        g = json.loads(out_json.read_text())
        ids = [n["id"] for n in g.get("nodes", [])]
        assertion("graph build: no README pseudo-node in nodes",
                  "README" not in ids)
        assertion("graph build: no duplicate ids on empty template",
                  len(ids) == len(set(ids)),
                  f"duplicates: {[i for i in ids if ids.count(i) > 1][:5]}")
    finally:
        shutil.rmtree(out_json.parent, ignore_errors=True)


def test_repo_root_tooling():
    """Tools that resolve via dirname(dataDir) need dataDir to be a direct
    child of the repo root. Use the empty org/ starter for those.
    """
    real_org = REPO_ROOT / "org"
    d = str(real_org)

    # ---- org_skills_list ----
    out = call(d, "org_skills_list", {})
    parsed = json.loads(out)
    names = {s["name"] for s in parsed.get("skills", [])}
    expected = {"init", "ingest", "lint", "compile-agent", "interview-activity",
                "ai-exposure", "value-map", "reshuffle", "world-model", "graph",
                "new-playbook"}
    assertion(f"skills_list exposes all 11 skills (got {len(names)})",
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

    # ---- org_lint_run Tier 2 — semantic checks ----
    # Locks the typo fix (was `ORG = ROOT / "Org"` which silently broke on
    # case-sensitive filesystems) and the --org-dir CLI flag both scripts
    # now accept. The empty starter has 3 identity stubs, so Tier 2 returns
    # 0 metrics violations — what we assert is that the script ran cleanly.
    out = call(d, "org_lint_run", {"tier": "tier2"})
    parsed = json.loads(out)
    assertion("lint_run tier2 exit_code is 0",
              parsed.get("tier2", {}).get("exit_code") == 0,
              parsed.get("tier2", {}).get("stderr", "")[:200])
    assertion("lint_run tier2 returns a report path",
              str(parsed.get("tier2", {}).get("summary", {}).get("report", "")).endswith(".md"),
              parsed.get("tier2", {}).get("summary", {}).get("report"))

    # ---- org_lint_run --tier both — both scripts run in one call ----
    out = call(d, "org_lint_run", {"tier": "both"})
    parsed = json.loads(out)
    assertion("lint_run both runs tier1 cleanly",
              parsed.get("tier1", {}).get("exit_code") == 0)
    assertion("lint_run both runs tier2 cleanly",
              parsed.get("tier2", {}).get("exit_code") == 0)


    # ---- org_open ----
    out = call(d, "org_open", {"path": "org/log.md"})
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

    out = call(d, "org_open", {"path": "org/nonexistent-file-xyz.md"})
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
    run_section("Graph viewer design regression", test_graph_viewer_design_regression)
    run_section("ai-exposure viewer design regression", test_ai_exposure_viewer_design_regression)
    run_section("value-map viewer design regression", test_value_map_viewer_design_regression)
    run_section("reshuffle viewer design regression", test_reshuffle_viewer_design_regression)
    run_section("world-model viewer design regression", test_world_model_viewer_design_regression)
    run_section("value-map end_user normalization (dict / str / list)", test_value_map_end_user_normalization)
    run_section("design.inline_md (markdown in agent prose)", test_design_inline_md)
    run_section("graph viewer --lang it (chrome + About modal in Italian)", test_graph_viewer_lang_it)
    run_section("graph autoresearch failure modes (locks 5 leaks from AIRC iteration)", test_graph_autoresearch_failure_modes)
    run_section("graph build skips README folder-doc stubs", test_graph_build_skips_readme_stubs)
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
