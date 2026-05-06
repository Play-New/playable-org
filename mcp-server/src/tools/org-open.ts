/**
 * org_open — open a file inside the bundled repository in the OS default app.
 *
 * Used so the agent can show a value-map / reshuffle / world-model HTML to the
 * user without forcing them to navigate the filesystem. macOS uses `open`,
 * Linux `xdg-open`, Windows `start`. The path is constrained to the repo
 * directory (dataDir's parent) — no opening of arbitrary system files.
 */

import { spawn } from 'node:child_process';
import { dirname, resolve } from 'node:path';
import { access } from 'node:fs/promises';
import { z } from 'zod';

import type { ToolDefinition } from '../server.js';
import { safeResolve, PathTraversalError } from '../lib/safe-path.js';

const inputSchema = {
  type: 'object',
  properties: {
    path: {
      type: 'string',
      description:
        'Path to the file to open, relative to the repo root (e.g. "Org/plays/data/value-map-X-2026-05-05.html"). Must resolve inside the bundled repo; absolute paths or paths escaping the repo are rejected.',
    },
  },
  required: ['path'],
} as const;

const ArgsSchema = z.object({ path: z.string().min(1) });

function openCommand(): { cmd: string; args: (p: string) => string[] } {
  if (process.platform === 'darwin') {
    return { cmd: 'open', args: (p) => [p] };
  }
  if (process.platform === 'win32') {
    // Use cmd /c start "" "<path>"; the empty quoted "" is the window title.
    return { cmd: 'cmd', args: (p) => ['/c', 'start', '""', p] };
  }
  return { cmd: 'xdg-open', args: (p) => [p] };
}

export const orgOpenTool: ToolDefinition = {
  name: 'org_open',
  description:
    "Open a file from the bundled repo in the user's default OS application (browser for HTML, image viewer for SVG/PNG, PDF reader for PDF). Use this when the user asks to see/open the artefact a playbook has just produced. The path argument is the path returned by org_play_run (e.g. \"Org/plays/data/...html\"); it must be inside the repo. Returns ok with the resolved absolute path, or an error if the file does not exist or is outside the repo.",
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { path } = ArgsSchema.parse(rawArgs);
    const repoRoot = dirname(ctx.dataDir);

    let absPath: string;
    try {
      absPath = safeResolve(repoRoot, path);
    } catch (e) {
      if (e instanceof PathTraversalError) {
        return {
          content: [{ type: 'text', text: `Error: path "${path}" escapes the repo root.` }],
        };
      }
      throw e;
    }

    try {
      await access(absPath);
    } catch {
      return {
        content: [{ type: 'text', text: `Error: file does not exist at ${absPath}.` }],
      };
    }

    const { cmd, args: argFn } = openCommand();
    const proc = spawn(cmd, argFn(absPath), { detached: true, stdio: 'ignore' });
    proc.unref();

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              ok: true,
              opened: absPath,
              file_url: `file://${absPath}`,
              platform: process.platform,
            },
            null,
            2
          ),
        },
      ],
    };
  },
};
