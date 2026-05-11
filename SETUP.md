# Setup

Instructions to connect Playable Org to Claude Desktop. Works on **Windows** and **macOS**. After install, Claude can read your structure and answer questions citing the sources you've fed it.

The template runs as an MCP server inside **Claude Desktop**. Local MCP servers are a desktop-app feature today; claude.ai web supports remote connectors but not the local stdio path this installer registers.

## Prerequisites

- Windows 10/11 or recent macOS
- Claude Desktop installed (https://claude.ai/download)
- Node.js (the installer checks and tells you if it's missing)
- The `playable-org` folder downloaded from GitHub — see step 1

## The 3 steps

### 1. Get the folder

**From GitHub (recommended)**:

1. Open [github.com/Play-New/playable-org](https://github.com/Play-New/playable-org) in your browser.
2. Click the green **Code** button (top right of the file list), then **Download ZIP**.
3. Extract the zip:
   - **Windows**: right-click → _Extract All_ → confirm.
   - **macOS**: double-click the zip; the archive extracts automatically.
4. You'll get a folder named `playable-org-main`. The rest of these instructions refer to it simply as `playable-org` — rename it if you want, or leave the `-main` suffix.
5. Save the folder wherever you prefer (Desktop, Documents). Remember the path.

**From the command line** (if you have `git` installed):

```bash
git clone https://github.com/Play-New/playable-org.git
```

### 2. Run the installer

Open the `playable-org` folder and double-click the installer file:

- **Windows**: `install.bat`
- **macOS**: `install.command`

A window opens (Command Prompt on Windows, Terminal on macOS). The installer:

- builds the mcp server (TypeScript → JavaScript), about ten seconds
- registers the server in Claude Desktop's config:
  - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
  - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- touches nothing else in your system

Wait until you see:

```
Installation complete.
```

Close the window.

#### Possible warnings

**Windows — _"Windows protected your PC" / SmartScreen_**: click _More info_ → _Run anyway_. Standard Windows behaviour for locally-signed scripts.

**macOS — _"macOS cannot verify the developer"_**: right-click `install.command` → _Open_ → _Open_ in the confirmation dialog.

**_"command not found: node"_ (both platforms)**: download the _LTS Recommended_ version from https://nodejs.org. On Windows pick the `.msi`, on macOS the `.pkg`. Run the installer, accept defaults. Then re-run the Playable Org installer.

### 3. Restart Claude Desktop

- **Windows**: right-click the Claude icon in the taskbar → _Quit_; then reopen Claude Desktop from the Start menu.
- **macOS**: `Cmd+Q` to quit Claude, then reopen from Applications.

The restart is required because Claude reads its mcp configuration only at startup.

## Populate the structure

The graph ships empty. Before you can ask meaningful questions, you need to feed it source documents.

### Drop your sources

Open `playable-org/org/sources/` in Finder / File Explorer. Drag in any of:

- founding documents (charter, articles of association, statute)
- governance documents (governance charter, code of ethics, compliance framework)
- organizational charts (current and historical)
- role-description documents per area or division
- annual report or audited statements
- internal process documentation
- HR analyses or capability assessments

Acceptable formats: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.html`, `.txt`. Use kebab-case filenames (e.g., `articles-of-association-2024.pdf`).

### Run init

In a new chat in Claude Desktop:

> Initialize the structure.

Claude follows the `init` skill. Two starting paths, picked from what's available:

- **Path A — documents-first**: if you've dropped founding documents into `org/sources/`, Claude reads them in priority order (founding documents fill the three identity stubs first), then iterates through operational, stakeholder, and financial documents, proposing entities in batches, showing you the diff, writing on confirmation, appending one log line per batch.

- **Path B — interview-first**: if `org/sources/` is empty (or only has documents that don't cover the structure), Claude runs a structured ten-question interview. Your answers are saved verbatim as a source document (`init-interview-<date>.md`) and every node Claude writes cites that source. The principle stays: every assertion has a citation, the citation can be testimony.

The two paths can also combine: start with what documents exist, then fill gaps with a targeted interview anchored on what the documents leave unsaid.

A first session typically takes 30 to 60 minutes (Path A) or 20 to 40 minutes (Path B), and produces 50 to 400 nodes.

After init, run:

> Run the lint.

To verify the populated structure has no issues (broken citations, orphan nodes, missing fields).

## What you can ask

Once initialized, ask Claude in plain language. The system reads from your structure and answers with citations.

**Operational questions** (the kind that today require flipping through role-description documents or the org chart):

- "Show me the organizational structure: how many divisions and what areas do they contain."
- "What does area X do? Who leads it?"
- "Who handles relationship Y with stakeholder Z?"
- "Walk me through process W from start to finish, citing the sources."
- "Which areas are currently vacant or under interim leadership?"

**Integrity questions** (the kind that require comparing multiple documents):

- "Where are the documented fragilities in the organization?"
- "Show me overlaps or duplication of responsibilities."
- "What changed between the org chart of [date A] and the org chart of [date B]?"

**Financial questions** (if you have ingested financial data):

- "What is the revenue composition for [year]?"
- "How much did [line item] grow vs the previous year?"
- "How are operating costs distributed across divisions?"

**Analytical questions** (these trigger the playbooks):

- "Where is the X process going on the evolution curve, and where can AI change it?" (value-map)
- "What holds the Y bundle together today, and what changes if AI matures?" (reshuffle)
- "What are our key capabilities, which are differentiated craft, which are standard practice?" (world-model)
- "On which of our activities is AI already capable enough to help?" (ai-exposure)

Running a playbook produces a *play* — a frozen interactive HTML page that Claude generates and opens in your default browser. Plays accumulate under `org/plays/data/`; old plays are never overwritten.

When Claude doesn't know something, it says so — it does not invent.

## Adding a new document later

Drag the file into the chat and say:

> Ingest this document.

Claude follows the `ingest` skill: it identifies the source, proposes structure updates, asks for your confirmation before writing. Nothing changes without your approval.

## Open questions you might want to track

The agent appends to `org/open-questions.md` whenever it hits an ambiguity that needs an internal answer (an unclear acronym, a discrepancy between two sources, a gap in the chart). Open the file when you have 30 minutes:

```
playable-org/org/open-questions.md
```

It opens in your default text editor (Notepad on Windows, TextEdit on macOS).

## Help

Issues on GitHub: https://github.com/Play-New/playable-org/issues
