/**
 * org_play_run — execute a playbook pipeline against the bundled org/.
 *
 * Two modes:
 * - mode="build" — runs the script that walks the structure and produces
 *   the JSON skeleton (or, for ai-exposure, the embedding match).
 *   Returns the JSON content inline so the agent can read it / fill in
 *   the interpretive fields without having to round-trip the disk.
 * - mode="render" — given a filled JSON (provided by the agent in
 *   `json_content`), writes it to plays/data/, runs audit.py, runs
 *   viewer.py, and returns the artefact paths plus the audit result.
 *
 * For ai-exposure: mode="build" walks all activities, runs match.py end
 * to end, and writes both JSON and HTML — no agent fill needed.
 */

import { spawn } from 'node:child_process';
import { writeFile, readFile, mkdir, access } from 'node:fs/promises';
import { resolve, join } from 'node:path';
import { findRepoRoot } from '../lib/repo-root.js';
import { z } from 'zod';

import type { ToolDefinition } from '../server.js';

const inputSchema = {
  type: 'object',
  properties: {
    playbook: {
      type: 'string',
      enum: ['ai-exposure', 'value-map', 'reshuffle', 'world-model'],
      description: 'Which playbook to run.',
    },
    mode: {
      type: 'string',
      enum: ['build', 'render'],
      description:
        'build: walk structure, produce skeleton (or full pipeline for ai-exposure). render: take the agent-filled JSON in json_content and produce audit + viewer.',
    },
    anchor: {
      type: 'string',
      description:
        'For value-map and reshuffle: the commitment id or unit id the slice is anchored on. For world-model: ignored. For ai-exposure: ignored (always full org).',
    },
    kind: {
      type: 'string',
      enum: ['commitment', 'unit'],
      description: 'Anchor kind for value-map / reshuffle.',
    },
    scope: {
      type: 'string',
      description:
        'World-model only: optional unit id to scope the analysis (default: full org).',
    },
    json_content: {
      type: 'string',
      description:
        'Required when mode=render. The full JSON content (string) the agent has filled.',
    },
    out_name: {
      type: 'string',
      description:
        'Optional artefact base name (default: "<playbook>-<anchor-or-scope>-<YYYY-MM-DD>").',
    },
  },
  required: ['playbook', 'mode'],
} as const;

const ArgsSchema = z
  .object({
    playbook: z.enum(['ai-exposure', 'value-map', 'reshuffle', 'world-model']),
    mode: z.enum(['build', 'render']),
    anchor: z.string().optional(),
    kind: z.enum(['commitment', 'unit']).optional(),
    scope: z.string().optional(),
    json_content: z.string().optional(),
    out_name: z.string().optional(),
  })
  .refine((d) => d.mode !== 'render' || !!d.json_content, {
    message: 'json_content required when mode=render',
  });

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

function today(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

async function ensureDir(p: string): Promise<void> {
  await mkdir(p, { recursive: true });
}

export const orgPlayRunTool: ToolDefinition = {
  name: 'org_play_run',
  description:
    'Execute a playbook pipeline (ai-exposure / value-map / reshuffle / world-model). mode=build walks the structure and returns a JSON skeleton (for ai-exposure: runs the full match + viewer end to end). mode=render takes a filled JSON in json_content, writes it to plays/data/, runs audit.py and viewer.py, and returns the resulting artefact paths plus the audit summary. Spawns python3; requires Python 3 in PATH on the customer machine.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const args = ArgsSchema.parse(rawArgs);
    const repoRoot = await findRepoRoot(ctx.dataDir);
    const playbookDir = resolve(repoRoot, 'skills', 'playbooks', args.playbook);
    const dataDir = resolve(ctx.dataDir, 'plays', 'data');
    await ensureDir(dataDir);

    const baseName =
      args.out_name ??
      `${args.playbook}-${args.anchor ?? args.scope ?? 'airc'}-${today()}`;
    const jsonPath = join(dataDir, `${baseName}.json`);
    const htmlPath = join(dataDir, `${baseName}.html`);
    const svgPath = join(dataDir, `${baseName}.svg`);

    // ----------------------------- BUILD MODE ----------------------------
    if (args.mode === 'build') {
      // ai-exposure: build needs an activities JSON first; simplest path is
      // to surface the full all-org match that's already in the bundle, plus
      // the rich activities metadata. Re-running match.py is expensive
      // (loads the embedding model) — defer that to a future "rematch"
      // dedicated tool. For now build mode = "use the cached match".
      if (args.playbook === 'ai-exposure') {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                {
                  status: 'noop',
                  reason:
                    'ai-exposure build is precomputed in plays/data/all-org-matches-2026-05-03.json. Pass it to mode=render with json_content set to the file content (or use the existing artefact) to regenerate the HTML viewer.',
                },
                null,
                2
              ),
            },
          ],
        };
      }

      // value-map / reshuffle / world-model build
      const buildScript = resolve(playbookDir, 'build.py');
      try {
        await access(buildScript);
      } catch {
        return {
          content: [{ type: 'text', text: `Error: build.py not found at ${buildScript}.` }],
        };
      }

      const cliArgs: string[] = [buildScript];
      if (args.playbook === 'value-map') {
        if (!args.anchor || !args.kind) {
          return {
            content: [
              { type: 'text', text: 'Error: value-map build requires anchor + kind.' },
            ],
          };
        }
        cliArgs.push('--anchor', args.anchor, '--kind', args.kind);
        cliArgs.push('--ai-exposure-matches', resolve(dataDir, 'all-org-matches-2026-05-03.json'));
      } else if (args.playbook === 'reshuffle') {
        if (!args.anchor || !args.kind) {
          return {
            content: [
              { type: 'text', text: 'Error: reshuffle build requires anchor (slice) + kind.' },
            ],
          };
        }
        cliArgs.push('--slice', args.anchor, '--kind', args.kind);
        cliArgs.push('--ai-exposure-matches', resolve(dataDir, 'all-org-matches-2026-05-03.json'));
      } else if (args.playbook === 'world-model') {
        if (args.scope) cliArgs.push('--scope', args.scope);
        cliArgs.push('--ai-exposure-matches', resolve(dataDir, 'all-org-matches-2026-05-03.json'));
      }
      cliArgs.push('--org-dir', ctx.dataDir, '--out', jsonPath);

      const r = await runPython(cliArgs, repoRoot);
      if (r.exit_code !== 0) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(
                { status: 'error', stage: 'build', exit_code: r.exit_code, stderr: r.stderr.slice(0, 2000) },
                null,
                2
              ),
            },
          ],
        };
      }

      const skeletonText = await readFile(jsonPath, 'utf-8');
      let skeleton: unknown;
      try {
        skeleton = JSON.parse(skeletonText);
      } catch {
        skeleton = skeletonText;
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(
              {
                status: 'ok',
                stage: 'build',
                json_path: jsonPath.replace(repoRoot + '/', ''),
                skeleton,
                next_step:
                  'Fill in the agent-interpretive fields per the SKILL.md (org_skill_read) for this playbook, then call org_play_run with mode=render and json_content set to the filled JSON.',
              },
              null,
              2
            ),
          },
        ],
      };
    }

    // ----------------------------- RENDER MODE ---------------------------
    // Validate JSON parses
    try {
      JSON.parse(args.json_content!);
    } catch (e) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: json_content is not valid JSON: ${(e as Error).message}`,
          },
        ],
      };
    }

    await writeFile(jsonPath, args.json_content!, 'utf-8');

    const auditScript = resolve(playbookDir, 'audit.py');
    const viewerScript = resolve(playbookDir, 'viewer.py');

    // Audit
    const auditArgs: string[] = [auditScript, '--map', jsonPath, '--org-dir', ctx.dataDir];
    const auditResult = await runPython(auditArgs, repoRoot);

    // Viewer — flag shape differs by playbook.
    // value-map / world-model / reshuffle: --map ... --html ...
    // ai-exposure: --matches ... --out ... (its CLI predates the
    //   --map convention; matches.json is the input shape it expects).
    // The viewer reads `decisions[]` directly from the input JSON when
    // present, so no separate --decisions plumbing is needed here.
    const viewerArgs: string[] = [viewerScript];
    if (args.playbook === 'ai-exposure') {
      viewerArgs.push('--matches', jsonPath, '--out', htmlPath);
    } else {
      viewerArgs.push('--map', jsonPath, '--html', htmlPath);
      if (args.playbook === 'value-map') {
        viewerArgs.push('--svg', svgPath);
      }
    }
    const viewerResult = await runPython(viewerArgs, repoRoot);

    const htmlOk = viewerResult.exit_code === 0;
    const svgOk = args.playbook === 'value-map' && htmlOk;

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              status: htmlOk ? 'ok' : 'partial',
              stage: 'render',
              artefacts: {
                json: jsonPath.replace(repoRoot + '/', ''),
                html: htmlOk ? htmlPath.replace(repoRoot + '/', '') : null,
                svg: svgOk ? svgPath.replace(repoRoot + '/', '') : null,
              },
              // Absolute file:// URLs the agent can paste back to the user as
              // clickable links in chat. Claude Desktop renders these as
              // openable links so the recipient doesn't have to navigate the
              // filesystem manually.
              file_urls: {
                json: `file://${jsonPath}`,
                html: htmlOk ? `file://${htmlPath}` : null,
                svg: svgOk ? `file://${svgPath}` : null,
              },
              audit: {
                exit_code: auditResult.exit_code,
                pass: auditResult.exit_code === 0,
                stdout_tail: auditResult.stdout.split('\n').slice(-12).join('\n'),
                stderr: auditResult.stderr.slice(0, 1500),
              },
              viewer: {
                exit_code: viewerResult.exit_code,
                stdout_tail: viewerResult.stdout.split('\n').slice(-3).join('\n'),
                stderr: viewerResult.stderr.slice(0, 1500),
              },
              presentation_markdown:
                htmlOk
                  ? `[Apri nel browser](file://${htmlPath})`
                  : null,
              presentation_hint:
                htmlOk
                  ? 'IMPORTANT: (1) Immediately call org_open with the relative html path (artefacts.html) to open the file in the default browser — the recipient should see the artefact without further interaction. (2) In your text reply, include the presentation_markdown string VERBATIM (do not paraphrase, do not wrap in code, just paste the [text](file://...) Markdown link as-is so it renders as a clickable link). (3) Do NOT inline-render the SVG as a widget — the HTML opened in step 1 is the canonical visualization.'
                  : 'Render failed; show the user the audit/viewer stderr verbatim.',
            },
            null,
            2
          ),
        },
      ],
    };
  },
};
