/**
 * org_log_append — append a line to org/log.md.
 *
 * The log is append-only per AGENTS.md. Each entry is one line, prefixed
 * with the current date in ISO format (YYYY-MM-DD). The caller passes the
 * entry text without the date.
 */

import { appendFile, access } from 'node:fs/promises';
import { z } from 'zod';

import type { ToolDefinition } from '../server.js';
import { safeResolve } from '../lib/safe-path.js';

const inputSchema = {
  type: 'object',
  properties: {
    entry: {
      type: 'string',
      description:
        'Log entry text. Will be prefixed with current date (YYYY-MM-DD) and "—". Should be one line; newlines will be collapsed to spaces.',
    },
    date: {
      type: 'string',
      description: 'Optional override for the date prefix (ISO format YYYY-MM-DD). Default: today.',
    },
  },
  required: ['entry'],
} as const;

const ArgsSchema = z.object({
  entry: z.string().min(1),
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
});

function todayISO(): string {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

export const orgLogAppendTool: ToolDefinition = {
  name: 'org_log_append',
  description:
    'Append one line to org/log.md (append-only audit). Prefixes the entry with current date (YYYY-MM-DD) and "—". Newlines in the entry are collapsed to spaces.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { entry, date } = ArgsSchema.parse(rawArgs);
    const prefix = date ?? todayISO();
    const flat = entry.replace(/\s*\n\s*/g, ' ').trim();
    if (!flat) {
      return { content: [{ type: 'text', text: 'Error: entry is empty after normalization.' }] };
    }

    const absPath = safeResolve(ctx.dataDir, 'log.md');
    // Ensure log.md exists (if not, create empty)
    try {
      await access(absPath);
    } catch {
      await appendFile(absPath, '# log\n\n', 'utf-8');
    }

    const line = `${prefix} — ${flat}\n`;
    await appendFile(absPath, line, 'utf-8');

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ ok: true, line: line.trim() }, null, 2),
        },
      ],
    };
  },
};
