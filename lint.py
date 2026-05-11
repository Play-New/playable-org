#!/usr/bin/env python3
"""Mechanical lint for Playable Org. Tier 1 — deterministic checks, no LLM.

Defaults to linting `<repo-root>/org/`. Pass `--org-dir <path>` to lint a
different directory (useful for forks that mount their structure under a
different name, or for linting the bundled sample-org fixture from this
template's CI). The report is written next to the org dir's parent by
default (`<parent>/lint-report-<date>.md`); pass `--report <path>` to
override.
"""
import argparse
import os
import re
import sys
from pathlib import Path
from collections import defaultdict
import datetime

ROOT = Path(__file__).parent

# Resolved at the bottom of the file from CLI args, before any walking.
ORG: Path = ROOT / "org"
REPORT: Path = ROOT / f"lint-report-{datetime.date.today()}.md"


def all_md_files():
    """All .md files under org/, excluding sources/, and excluding log.md."""
    for p in ORG.rglob("*.md"):
        rel = p.relative_to(ORG)
        if rel.parts and rel.parts[0] == "sources":
            continue
        if p.name == "log.md":
            continue
        yield p


def parse_frontmatter(content):
    """Manual frontmatter parser. Returns (dict, body_offset) or (None, 0)."""
    if not content.startswith("---\n"):
        return None, 0
    end = content.find("\n---\n", 4)
    if end == -1:
        # Try with trailing line at EOF
        end = content.find("\n---", 4)
        if end == -1 or end + 4 < len(content):
            return None, 0
    fm_text = content[4:end]
    fm = {}
    current_key = None

    for raw_line in fm_text.split("\n"):
        line = raw_line.rstrip()
        if not line.strip() or line.strip().startswith("#"):
            continue

        # Top-level key: value
        m = re.match(r"^([a-zA-Z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            key = m.group(1)
            value = m.group(2).strip()
            current_key = key

            if value == "":
                # Multi-line list follows (or empty)
                fm[key] = []
            elif value == "null" or value.lower() == "null":
                fm[key] = None
            elif value.startswith("[") and value.endswith("]"):
                # Inline list: [a, b, c]
                inner = value[1:-1].strip()
                if inner == "":
                    fm[key] = []
                else:
                    items = [s.strip().strip("\"'") for s in inner.split(",")]
                    fm[key] = items
            elif value.startswith("\"") and value.endswith("\""):
                fm[key] = value[1:-1]
            else:
                fm[key] = value
            continue

        # List item: "  - value" (under current_key)
        m = re.match(r"^\s+-\s+(.+)$", line)
        if m and current_key and isinstance(fm.get(current_key), list):
            item = m.group(1).strip().strip("\"'")
            fm[current_key].append(item)
            continue

    body_start = end + 5  # skip past "\n---\n"
    return fm, body_start


def main():
    nodes = {}  # id -> {file, frontmatter, body}
    ids_by_file = {}  # file -> id
    no_frontmatter = []  # files without parseable frontmatter (e.g., README, AGENTS, index)
    markdown_links = []  # (file, line_num, text, path)

    md_link_re = re.compile(r"\[([^\[\]]+)\]\(([^()]+\.md)\)")

    # Files we don't expect to have node-frontmatter
    metadata_files = {"README.md", "AGENTS.md", "index.md", "open-questions.md"}

    for f in all_md_files():
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"Failed to read {f}: {e}", file=sys.stderr)
            continue

        fm, body_start = parse_frontmatter(content)
        if fm and "id" in fm:
            node_id = fm["id"]
            nodes[node_id] = {"file": f, "frontmatter": fm, "body": content[body_start:]}
            ids_by_file[f] = node_id
        elif f.name not in metadata_files:
            no_frontmatter.append(f)

        # Find markdown links to .md files (skip fenced code blocks AND inline code spans)
        in_code_block = False
        for line_num, line in enumerate(content.split("\n"), 1):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            # Strip inline code spans (text between single backticks) before scanning links
            line_no_code = re.sub(r"`[^`]*`", "", line)
            for m in md_link_re.finditer(line_no_code):
                text = m.group(1)
                path = m.group(2)
                if path.startswith(("http://", "https://")):
                    continue
                markdown_links.append((f, line_num, text, path))

    # === Check 1: broken markdown links ===
    broken_links = []
    for src, line_num, text, path in markdown_links:
        target = (src.parent / path).resolve()
        if not target.exists():
            broken_links.append((src, line_num, text, path, target))

    # === Check 2: ID uniqueness ===
    id_counts = defaultdict(list)
    for f, id_ in ids_by_file.items():
        id_counts[id_].append(f)
    duplicate_ids = {i: fs for i, fs in id_counts.items() if len(fs) > 1}

    # === Check 3: filename matches id ===
    filename_mismatches = []
    for f, id_ in ids_by_file.items():
        expected = f"{id_}.md"
        if f.name != expected:
            filename_mismatches.append((f, id_, expected))

    # === Check 4: required frontmatter fields per type ===
    required_fields = {
        "unit": ["id", "type", "parent", "level", "description", "sources"],
        "person": ["id", "type", "role", "unit", "description", "sources"],
        "role": ["id", "type", "unit", "description", "sources"],
        "activity": ["id", "type", "performer", "unit", "description", "sources"],
        "stakeholder": ["id", "type", "kind", "description", "sources"],
        "commitment": ["id", "type", "parties_committing", "parties_benefiting", "level", "state", "fallback", "lifecycle", "sources"],
        "language-term": ["id", "type", "description", "sources"],
        "identity": ["id", "type", "description", "sources"],
    }
    frontmatter_issues = []
    for node_id, data in nodes.items():
        fm = data["frontmatter"]
        type_ = fm.get("type")
        if type_ in required_fields:
            for field in required_fields[type_]:
                if field not in fm:
                    frontmatter_issues.append((data["file"], node_id, type_, field))
                elif fm[field] in ("", []):
                    # empty string or empty list = incomplete
                    frontmatter_issues.append((data["file"], node_id, type_, field))
                # None (explicit null) is acceptable
        elif type_ is None:
            frontmatter_issues.append((data["file"], node_id, "<missing>", "type"))

    # === Check 5: cross-reference validity ===
    xref_issues = []
    for node_id, data in nodes.items():
        fm = data["frontmatter"]
        type_ = fm.get("type")

        def check(key, value, expected_types=None):
            if value is None or value == "" or value == "null":
                return
            if isinstance(value, list):
                for v in value:
                    check(key, v, expected_types)
                return
            if value not in nodes:
                xref_issues.append((data["file"], node_id, f"{key}='{value}' not found in any node"))
                return
            if expected_types:
                target_type = nodes[value]["frontmatter"].get("type")
                if target_type not in expected_types:
                    xref_issues.append(
                        (data["file"], node_id,
                         f"{key}='{value}' is type '{target_type}', expected {expected_types}")
                    )

        if type_ == "unit":
            check("parent", fm.get("parent"), ["unit"])
            check("head_role", fm.get("head_role"), ["role"])
        elif type_ == "person":
            check("role", fm.get("role"), ["role"])
            check("unit", fm.get("unit"), ["unit"])
        elif type_ == "role":
            check("unit", fm.get("unit"), ["unit"])
            check("reports_to", fm.get("reports_to"), ["role"])
            check("activities", fm.get("activities"), ["activity"])
        elif type_ == "activity":
            performer = fm.get("performer")
            if performer:
                if performer not in nodes:
                    xref_issues.append((data["file"], node_id, f"performer='{performer}' not found"))
                else:
                    pt = nodes[performer]["frontmatter"].get("type")
                    if pt not in ("role", "person"):
                        xref_issues.append((data["file"], node_id, f"performer='{performer}' is type '{pt}', expected role or person"))
            check("unit", fm.get("unit"), ["unit"])
        elif type_ == "commitment":
            check("parties_committing", fm.get("parties_committing"))
            check("parties_benefiting", fm.get("parties_benefiting"))
        elif type_ == "language-term":
            check("related", fm.get("related"))

    # === Check 6: parent-child symmetry on units ===
    # If unit A has parent: B, then B should be a unit (already checked in xref)
    # No extra check needed here

    # === Check 7: orphan nodes (no inbound link from frontmatter or body) ===
    inbound = defaultdict(int)
    for node_id, data in nodes.items():
        fm = data["frontmatter"]
        # Frontmatter references
        for key, value in fm.items():
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, str) and v in nodes:
                        inbound[v] += 1
            elif isinstance(value, str) and value in nodes:
                inbound[value] += 1
        # Body links
        body = data["body"]
        for m in md_link_re.finditer(body):
            path = m.group(2)
            if path.startswith(("http://", "https://")):
                continue
            target = (data["file"].parent / path).resolve()
            for tid, tdata in nodes.items():
                if tdata["file"].resolve() == target:
                    inbound[tid] += 1
                    break

    orphans = [
        (data["file"], node_id, fm.get("type"))
        for node_id, data in nodes.items()
        for fm in [data["frontmatter"]]
        if inbound.get(node_id, 0) == 0
        and fm.get("type") not in ("identity",)  # identity files are root-level
    ]

    # === Write report ===
    with open(REPORT, "w") as out:
        out.write(f"# Lint Report — {datetime.date.today()}\n\n")
        out.write(f"Nodes scanned: **{len(nodes)}**\n\n")

        out.write("## Summary\n\n")
        out.write(f"| Check | Issues |\n|---|---|\n")
        out.write(f"| Broken markdown links | {len(broken_links)} |\n")
        out.write(f"| Duplicate IDs | {len(duplicate_ids)} |\n")
        out.write(f"| Filename mismatches | {len(filename_mismatches)} |\n")
        out.write(f"| Frontmatter issues | {len(frontmatter_issues)} |\n")
        out.write(f"| Cross-reference issues | {len(xref_issues)} |\n")
        out.write(f"| Files without parseable frontmatter | {len(no_frontmatter)} |\n")
        out.write(f"| Orphan nodes (no inbound) | {len(orphans)} |\n")
        out.write("\n---\n\n")

        out.write("## 1. Broken markdown links\n\n")
        if broken_links:
            for src, line, text, path, target in broken_links[:200]:
                rel = src.relative_to(ORG)
                out.write(f"- `{rel}` line {line}: `[{text}]({path})`\n")
            if len(broken_links) > 200:
                out.write(f"\n*... and {len(broken_links) - 200} more*\n")
        else:
            out.write("(none)\n")
        out.write("\n")

        out.write("## 2. Duplicate IDs\n\n")
        if duplicate_ids:
            for id_, files in duplicate_ids.items():
                out.write(f"- `{id_}`:\n")
                for f in files:
                    out.write(f"  - `{f.relative_to(ORG)}`\n")
        else:
            out.write("(none)\n")
        out.write("\n")

        out.write("## 3. Filename mismatches\n\n")
        if filename_mismatches:
            for file, id_, expected in filename_mismatches:
                out.write(f"- `{file.relative_to(ORG)}` has id `{id_}`, expected filename `{expected}`\n")
        else:
            out.write("(none)\n")
        out.write("\n")

        out.write("## 4. Frontmatter issues (missing required fields)\n\n")
        if frontmatter_issues:
            for file, id_, type_, field in frontmatter_issues:
                out.write(f"- `{file.relative_to(ORG)}` (id: `{id_}`, type: `{type_}`): missing `{field}`\n")
        else:
            out.write("(none)\n")
        out.write("\n")

        out.write("## 5. Cross-reference issues\n\n")
        if xref_issues:
            for file, id_, msg in xref_issues:
                out.write(f"- `{file.relative_to(ORG)}` (id: `{id_}`): {msg}\n")
        else:
            out.write("(none)\n")
        out.write("\n")

        out.write("## 6. Files without parseable frontmatter\n\n")
        if no_frontmatter:
            for f in no_frontmatter:
                out.write(f"- `{f.relative_to(ORG)}`\n")
        else:
            out.write("(none)\n")
        out.write("\n")

        out.write("## 7. Orphan nodes (no inbound references)\n\n")
        out.write("*Note: nodes without inbound references could be missing cross-links or genuinely standalone.*\n\n")
        if orphans:
            for file, id_, type_ in orphans:
                out.write(f"- `{file.relative_to(ORG)}` (id: `{id_}`, type: `{type_}`)\n")
        else:
            out.write("(none)\n")
        out.write("\n")

    print(f"Report: {REPORT}")
    print(f"Nodes: {len(nodes)}")
    print(f"Broken links: {len(broken_links)}")
    print(f"Duplicate IDs: {len(duplicate_ids)}")
    print(f"Filename mismatches: {len(filename_mismatches)}")
    print(f"Frontmatter issues: {len(frontmatter_issues)}")
    print(f"Cross-reference issues: {len(xref_issues)}")
    print(f"No frontmatter: {len(no_frontmatter)}")
    print(f"Orphan nodes: {len(orphans)}")


def _resolve_paths_from_argv() -> None:
    """Apply --org-dir / --report to the module-level ORG and REPORT
    before main() walks the filesystem."""
    global ORG, REPORT
    parser = argparse.ArgumentParser(
        description="Tier-1 mechanical lint of an org/ directory.",
    )
    parser.add_argument(
        "--org-dir",
        type=Path,
        default=ROOT / "org",
        help="Directory to lint (default: <repo-root>/org).",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Where to write the markdown report (default: <repo-root>/lint-report-<date>.md).",
    )
    args = parser.parse_args()
    ORG = args.org_dir.resolve()
    if not ORG.is_dir():
        sys.stderr.write(f"lint: org dir not found: {ORG}\n")
        sys.exit(2)
    REPORT = (
        args.report.resolve()
        if args.report
        else ROOT / f"lint-report-{datetime.date.today()}.md"
    )


if __name__ == "__main__":
    _resolve_paths_from_argv()
    main()
