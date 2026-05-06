/**
 * org_lint_run — run the lint scripts (Tier 1 + Tier 2) and return the report.
 *
 * Spawns python3 against the bundled lint.py and lint-semantic.py at the
 * repo root. Captures stdout/stderr, returns a structured summary.
 *
 * Requires Python 3 to be available in the customer's PATH (the install
 * script verifies Node.js but Python is on the customer; if missing, the
 * tool returns a clear error so the agent can tell the user).
 */

import { spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { access } from 'node:fs/promises';

import type { ToolDefinition } from '../server.js';

const inputSchema = {
  type: 'object',
  properties: {
    tier: {
      type: 'string',
      enum: ['tier1', 'tier2', 'both'],
      description: 'Which tier to run. Default "both".',
    },
  },
} as const;

interface RunResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

function runScript(scriptAbs: string, repoRoot: string): Promise<RunResult> {
  return new Promise((resolveP) => {
    const proc = spawn('python3', [scriptAbs], { cwd: repoRoot });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', (b) => (stdout += b.toString()));
    proc.stderr.on('data', (b) => (stderr += b.toString()));
    proc.on('error', (err) => {
      resolveP({ exit_code: -1, stdout, stderr: stderr + String(err) });
    });
    proc.on('close', (code) => {
      resolveP({ exit_code: code ?? -1, stdout, stderr });
    });
  });
}

function parseTier1Summary(stdout: string): Record<string, number | string> {
  const out: Record<string, number | string> = {};
  for (const line of stdout.split('\n')) {
    const m = line.match(/^([A-Za-z][A-Za-z ↔→ -]+?):\s+(\d+)\s*$/);
    if (m) out[m[1].trim()] = Number(m[2]);
    const r = line.match(/^Report:\s+(.+)$/);
    if (r) out['report'] = r[1].trim();
  }
  return out;
}

export const orgLintRunTool: ToolDefinition = {
  name: 'org_lint_run',
  description:
    "Run the lint scripts (Tier 1 = structural, Tier 2 = semantic) on the bundled org/. Spawns python3 against the bundled lint.py and lint-semantic.py. Returns parsed counts per check and the path to the dated lint report file. Requires Python 3 in PATH on the customer machine; if missing, returns a clear error so the agent can ask the user to install it.",
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const tier = (rawArgs as { tier?: string })?.tier ?? 'both';
    const repoRoot = dirname(ctx.dataDir);

    const scripts: Array<{ key: string; path: string }> = [];
    if (tier === 'tier1' || tier === 'both') {
      scripts.push({ key: 'tier1', path: resolve(repoRoot, 'lint.py') });
    }
    if (tier === 'tier2' || tier === 'both') {
      scripts.push({ key: 'tier2', path: resolve(repoRoot, 'lint-semantic.py') });
    }

    // Pre-flight: scripts exist
    for (const s of scripts) {
      try {
        await access(s.path);
      } catch {
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${s.key} script missing at ${s.path}. The bundle may be incomplete.`,
            },
          ],
        };
      }
    }

    const results: Record<string, RunResult & { summary?: Record<string, number | string> }> = {};
    for (const s of scripts) {
      const r = await runScript(s.path, repoRoot);
      const summary = parseTier1Summary(r.stdout);
      results[s.key] = { ...r, summary };
    }

    // Friendly Python-missing detection
    const allFailed = Object.values(results).every((r) => r.exit_code !== 0);
    const looksLikePythonMissing =
      allFailed &&
      Object.values(results).some(
        (r) => r.stderr.includes('ENOENT') || r.stderr.includes('command not found') || r.stderr.includes('No such file')
      );
    if (looksLikePythonMissing) {
      return {
        content: [
          {
            type: 'text',
            text: 'Error: python3 not found in PATH. Install Python 3 (LTS) from https://www.python.org/downloads/ and re-run the lint.',
          },
        ],
      };
    }

    return {
      content: [
        { type: 'text', text: JSON.stringify(results, null, 2) },
      ],
    };
  },
};
