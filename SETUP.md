# Setup

Instructions to connect Playable Org to Claude Desktop. Works on **Windows** and **macOS**. After install, Claude can read your structure and answer questions citing the sources you've fed it.

## Prerequisites

- Windows 10/11 or recent macOS
- Claude Desktop installed (https://claude.ai/download)
- Node.js (the installer checks and tells you if it's missing)
- The `playable-org` folder saved locally (zip received via email, or `git clone` if you have repo access)

## The 3 steps

### 1. Extract the folder

If you received a zip (`playable-org-<date>.zip`):

- **Windows**: right-click the zip → _Extract All_ → confirm. You'll get a `playable-org` folder.
- **macOS**: double-click the zip — the archive extracts automatically.

Save the `playable-org` folder wherever you prefer (Desktop, Documents, etc.). Remember the path.

If you cloned from git: skip to step 2.

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

Open `playable-org/Org/sources/` in Finder / File Explorer. Drag in any of:

- founding documents (charter, articles of association, statute)
- governance documents (governance charter, code of ethics, compliance framework)
- organizational charts (current and historical)
- role-description documents per area or division
- annual report or audited statements
- internal process documentation
- HR analyses or capability assessments

Acceptable formats: `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.md`, `.html`, `.txt`. Use kebab-case filenames (e.g., `articles-of-association-2024.pdf`).

### Run seed

In a new chat in Claude Desktop:

> Seed the structure from `sources/`.

Claude follows the `seed` skill. It reads founding documents first to fill the three identity stubs (`mission`, `limits`, `rules`), then iterates through the rest, proposing entities in batches, showing you the diff, writing on confirmation, appending one log line per batch. A first session typically takes 30 to 60 minutes and produces 200 to 400 nodes.

After seed, run:

> Run the lint.

To verify the populated structure has no issues (broken citations, orphan nodes, missing fields).

## What you can ask

Once seeded, ask Claude in plain language. The system reads from your structure and answers with citations.

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
- "What are our key capabilities, which are unique, which are commodity?" (world-model)
- "On which of our activities is AI already capable enough to help?" (ai-exposure)

The playbook output is an interactive HTML page that Claude generates and opens in your default browser.

When Claude doesn't know something, it says so — it does not invent.

## Adding a new document later

Drag the file into the chat and say:

> Ingest this document.

Claude follows the `ingest` skill: it identifies the source, proposes substrate updates, asks for your confirmation before writing. Nothing changes without your approval.

## Open questions you might want to track

The agent appends to `Org/open-questions.md` whenever it hits an ambiguity that needs an internal answer (an unclear acronym, a discrepancy between two sources, a gap in the chart). Open the file when you have 30 minutes:

```
playable-org/Org/open-questions.md
```

It opens in your default text editor (Notepad on Windows, TextEdit on macOS).

## Help

Issues on GitHub: https://github.com/[user]/playable-org/issues
