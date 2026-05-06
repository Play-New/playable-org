/**
 * org_write_node — create or update a node in Org/.
 *
 * Writes to nodes/, identity/, language/, commitments/, plays/.
 * Refuses to write to sources/ (immutable per AGENTS.md invariant #1).
 * Refuses to write to identity/ unless explicit force=true (slow-changing per AGENTS.md).
 *
 * Validates that frontmatter has at least `id` and `type`, and that the
 * id matches the filename slug (per AGENTS.md cross-reference convention).
 */

import { writeFile, mkdir, access } from 'node:fs/promises';
import { dirname } from 'node:path';
import { z } from 'zod';
import matter from 'gray-matter';

import type { ToolDefinition } from '../server.js';
import { safeResolve, PathTraversalError } from '../lib/safe-path.js';

const inputSchema = {
  type: 'object',
  properties: {
    path: {
      type: 'string',
      description:
        'Path relative to dataDir, including .md extension (e.g., "nodes/units/finance.md", "commitments/org-suppliers-baseline.md").',
    },
    frontmatter: {
      type: 'object',
      description:
        'YAML frontmatter as a JSON object. Must include `id` (kebab-case matching filename) and `type`.',
    },
    body: {
      type: 'string',
      description: 'Markdown body (without frontmatter delimiters). Free text.',
    },
    mode: {
      type: 'string',
      enum: ['create', 'update', 'upsert'],
      description: 'create = fail if exists; update = fail if not exists; upsert = either. Default: upsert.',
    },
    force_identity: {
      type: 'boolean',
      description: 'Set true to allow writes under identity/. Default false (identity is slow-changing).',
    },
  },
  required: ['path', 'frontmatter', 'body'],
} as const;

const ArgsSchema = z.object({
  path: z.string().min(1),
  frontmatter: z.record(z.unknown()),
  body: z.string(),
  mode: z.enum(['create', 'update', 'upsert']).optional(),
  force_identity: z.boolean().optional(),
});

const ALLOWED_TOPDIRS = ['nodes', 'identity', 'language', 'commitments', 'financials', 'plays'];

async function fileExists(p: string): Promise<boolean> {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

export const orgWriteNodeTool: ToolDefinition = {
  name: 'org_write_node',
  description:
    'Create or update a node markdown file in Org/. Writes are restricted to nodes/, identity/, language/, commitments/, plays/. Refuses sources/ (immutable). Refuses identity/ unless force_identity=true (slow-changing). Validates frontmatter has id+type and id matches filename slug.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const args = ArgsSchema.parse(rawArgs);
    const { path, frontmatter, body, mode = 'upsert', force_identity = false } = args;

    // Path validation
    const normPath = path.replace(/\\/g, '/').replace(/^\/+/, '').replace(/\/+$/, '');
    if (!normPath.endsWith('.md')) {
      return { content: [{ type: 'text', text: `Error: path must end with .md (got "${path}")` }] };
    }
    const segs = normPath.split('/');
    const topdir = segs[0];
    if (!ALLOWED_TOPDIRS.includes(topdir)) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: writes restricted to ${ALLOWED_TOPDIRS.join(', ')}/. Got "${topdir}/". Sources are immutable; log.md uses org_log_append.`,
          },
        ],
      };
    }
    if (topdir === 'identity' && !force_identity) {
      return {
        content: [
          {
            type: 'text',
            text: 'Error: identity/ is slow-changing. Pass force_identity=true to override.',
          },
        ],
      };
    }

    // Frontmatter validation
    if (typeof frontmatter.id !== 'string' || !frontmatter.id) {
      return { content: [{ type: 'text', text: 'Error: frontmatter must include `id` (string, kebab-case).' }] };
    }
    if (typeof frontmatter.type !== 'string' || !frontmatter.type) {
      return { content: [{ type: 'text', text: 'Error: frontmatter must include `type` (string).' }] };
    }
    const filenameSlug = segs[segs.length - 1].replace(/\.md$/, '');
    if (frontmatter.id !== filenameSlug) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: frontmatter.id ("${frontmatter.id}") must match filename slug ("${filenameSlug}").`,
          },
        ],
      };
    }

    let absPath: string;
    try {
      absPath = safeResolve(ctx.dataDir, normPath);
    } catch (e) {
      if (e instanceof PathTraversalError) {
        return { content: [{ type: 'text', text: e.message }] };
      }
      throw e;
    }
    const exists = await fileExists(absPath);

    if (mode === 'create' && exists) {
      return { content: [{ type: 'text', text: `Error: file exists (mode=create). Use update or upsert.` }] };
    }
    if (mode === 'update' && !exists) {
      return { content: [{ type: 'text', text: `Error: file does not exist (mode=update). Use create or upsert.` }] };
    }

    // Compose markdown using gray-matter
    const composed = matter.stringify(body.endsWith('\n') ? body : body + '\n', frontmatter);

    await mkdir(dirname(absPath), { recursive: true });
    await writeFile(absPath, composed, 'utf-8');

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ ok: true, path: normPath, action: exists ? 'updated' : 'created' }, null, 2),
        },
      ],
    };
  },
};
