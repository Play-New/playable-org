/**
 * org_autoresearch_run — run the autoresearch loop on a play artefact.
 *
 * Each playbook ships its own autoresearch.py with five dimensions
 * (recognizability, plain-language, decision-anchoring, audit-grounded,
 * + opt-in LLM judge). This tool routes a play file to the right
 * autoresearch script and returns the parsed result.
 *
 * The promotion (saved memory) was: autoresearch should feel like a
 * property of the structure itself, not an external CLI step. With
 * this tool, an agent that has just rendered a play can immediately
 * call org_autoresearch_run to get the score — same surface as
 * org_lint_run, no shelling-out from chat.
 */

import { spawn } from 'node:child_process';
import { resolve, basename } from 'node:path';
import { access } from 'node:fs/promises';

import type { ToolDefinition } from '../server.js';
import { findRepoRoot } from '../lib/repo-root.js';

const inputSchema = {
  type: 'object',
  properties: {
    play_path: {
      type: 'string',
      description:
        'Relative path to the play JSON, typically under org/plays/data/. The playbook is inferred from the filename prefix (graph-*, value-map-*, ai-exposure-*, world-model-*, reshuffle-*).',
    },
    playbook: {
      type: 'string',
      enum: ['graph', 'value-map', 'ai-exposure', 'world-model', 'reshuffle'],
      description:
        'Optional override when the filename does not carry the playbook prefix.',
    },
    llm: {
      type: 'boolean',
      description:
        'Run the LLM-judge dimension as well (Claude Sonnet 4.6). Requires ANTHROPIC_API_KEY in the environment; without it the dimension is skipped (PASS) so the call still works offline. Default false.',
    },
  },
  required: ['play_path'],
} as const;

interface RunResult {
  exit_code: number;
  stdout: string;
  stderr: string;
}

function runPython(args: string[], cwd: string): Promise<RunResult> {
  return new Promise((resolveP) => {
    const proc = spawn('python3', args, { cwd });
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

function inferPlaybook(filename: string): string | null {
  const base = basename(filename);
  if (base.startsWith('graph-')) return 'graph';
  if (base.startsWith('value-map-')) return 'value-map';
  if (base.startsWith('ai-exposure-')) return 'ai-exposure';
  if (base.startsWith('world-model-')) return 'world-model';
  if (base.startsWith('reshuffle-')) return 'reshuffle';
  return null;
}

function parseAutoresearchSummary(stdout: string): {
  overall: 'PASS' | 'FAIL' | 'UNKNOWN';
  dimensions: Array<{ name: string; status: 'PASS' | 'FAIL' | 'SKIP'; detail: string }>;
} {
  const dimensions: Array<{ name: string; status: 'PASS' | 'FAIL' | 'SKIP'; detail: string }> = [];
  let overall: 'PASS' | 'FAIL' | 'UNKNOWN' = 'UNKNOWN';

  for (const line of stdout.split('\n')) {
    // Match lines like:  [PASS]  recognizability  —  ...
    const m = line.match(/^\s*\[(PASS|FAIL)\]\s+([a-z][a-z\s]+?)\s+—\s+(.*)$/);
    if (m) {
      const detail = m[3].trim();
      const status: 'PASS' | 'FAIL' | 'SKIP' =
        detail.startsWith('skipped') ? 'SKIP' : (m[1] as 'PASS' | 'FAIL');
      dimensions.push({ name: m[2].trim(), status, detail });
    }
    if (/AUTORESEARCH PASS/.test(line)) overall = 'PASS';
    if (/AUTORESEARCH FAIL/.test(line)) overall = 'FAIL';
  }
  return { overall, dimensions };
}

export const orgAutoresearchRunTool: ToolDefinition = {
  name: 'org_autoresearch_run',
  description:
    'Run the autoresearch loop on a play artefact. Each playbook ships its own autoresearch.py that scores the play on four deterministic dimensions (recognizability, plain-language, decision-anchoring, audit-grounded) and an opt-in LLM-judge fifth dimension (Claude Sonnet 4.6, scores each decision on actionable / distinctive / readable). The tool figures out which playbook from the filename (or accepts an override), spawns python3 against the right autoresearch.py, parses the per-dimension PASS/FAIL/SKIP plus the overall, and returns a structured summary the agent can act on. Same shape as org_lint_run.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const args = rawArgs as { play_path: string; playbook?: string; llm?: boolean };
    const repoRoot = await findRepoRoot(ctx.dataDir);

    // Resolve play path: relative to dataDir or absolute
    const playPath = args.play_path.startsWith('/')
      ? args.play_path
      : resolve(ctx.dataDir, args.play_path);
    try {
      await access(playPath);
    } catch {
      return {
        content: [
          { type: 'text', text: `Error: play file not found at ${playPath}.` },
        ],
      };
    }

    // Determine playbook
    const playbook = args.playbook ?? inferPlaybook(playPath);
    if (!playbook) {
      return {
        content: [
          {
            type: 'text',
            text:
              `Error: could not infer playbook from filename "${basename(playPath)}". ` +
              `Pass playbook=graph | value-map | ai-exposure | world-model | reshuffle explicitly.`,
          },
        ],
      };
    }

    const scriptPath = resolve(repoRoot, 'skills', 'playbooks', playbook, 'autoresearch.py');
    try {
      await access(scriptPath);
    } catch {
      return {
        content: [
          { type: 'text', text: `Error: autoresearch.py not found at ${scriptPath}.` },
        ],
      };
    }

    // ai-exposure uses --play; the others use --map. Same convention as
    // their own CLI.
    const flag = playbook === 'ai-exposure' ? '--play' : '--map';
    const cliArgs: string[] = [scriptPath, flag, playPath, '--org-dir', ctx.dataDir];
    if (args.llm) cliArgs.push('--llm');

    const r = await runPython(cliArgs, repoRoot);

    if (r.exit_code === -1 && (r.stderr.includes('ENOENT') || r.stderr.includes('command not found'))) {
      return {
        content: [
          {
            type: 'text',
            text: 'Error: python3 not found in PATH. Install Python 3 (LTS) from https://www.python.org/downloads/ and re-run.',
          },
        ],
      };
    }

    const summary = parseAutoresearchSummary(r.stdout);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              playbook,
              play_path: args.play_path,
              llm_judge: !!args.llm,
              overall: summary.overall,
              dimensions: summary.dimensions,
              exit_code: r.exit_code,
              raw_stdout: r.stdout.slice(-4000),
            },
            null,
            2
          ),
        },
      ],
    };
  },
};
