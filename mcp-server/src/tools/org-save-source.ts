/**
 * org_save_source — save a new file to sources/ (immutable invariant).
 *
 * Refuses to overwrite an existing source file (sources/ is append-only per
 * AGENTS.md invariant #1). Canonicalizes the filename to kebab-case.
 *
 * For text content: pass `content` (UTF-8 string).
 * For binary content: pass `content_base64` instead.
 */

import { writeFile, access, mkdir } from 'node:fs/promises';
import { z } from 'zod';

import type { ToolDefinition } from '../server.js';
import { safeResolve, PathTraversalError } from '../lib/safe-path.js';

const inputSchema = {
  type: 'object',
  properties: {
    filename: {
      type: 'string',
      description:
        'Target filename including extension (e.g., "annual-report-2025.pdf", "org-chart.docx"). Will be canonicalized to kebab-case.',
    },
    content: {
      type: 'string',
      description: 'UTF-8 text content. Mutually exclusive with content_base64.',
    },
    content_base64: {
      type: 'string',
      description: 'Base64-encoded binary content. Use for PDFs, DOCX, XLSX, PPTX, images. Mutually exclusive with content.',
    },
  },
  required: ['filename'],
} as const;

const ArgsSchema = z
  .object({
    filename: z.string().min(1),
    content: z.string().optional(),
    content_base64: z.string().optional(),
  })
  .refine((d) => (d.content ? !d.content_base64 : !!d.content_base64), {
    message: 'Provide exactly one of `content` (text) or `content_base64` (binary).',
  });

function canonicalizeFilename(name: string): string {
  // Split extension
  const m = name.match(/^(.*?)(\.[a-zA-Z0-9]+)?$/);
  const stem = m?.[1] ?? name;
  const ext = m?.[2] ?? '';
  const slug = stem
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '') // strip diacritics
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug + ext.toLowerCase();
}

async function fileExists(p: string): Promise<boolean> {
  try {
    await access(p);
    return true;
  } catch {
    return false;
  }
}

export const orgSaveSourceTool: ToolDefinition = {
  name: 'org_save_source',
  description:
    'Save a new file to sources/. Sources are immutable: refuses to overwrite an existing file. Filename is canonicalized to kebab-case. Use `content` (UTF-8 text) or `content_base64` (binary).',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const args = ArgsSchema.parse(rawArgs);

    // Reject path-traversal attempts in raw input BEFORE canonicalization.
    // Canonicalize sterilizes the string but can mask attacker intent ("../../etc/x"
    // becoming "etc-x") which is misleading even though contained.
    if (args.filename.includes('/') || args.filename.includes('\\') || args.filename.includes('..')) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: filename must be a plain basename (no "/", "\\", or ".."). Got "${args.filename}".`,
          },
        ],
      };
    }

    const canonical = canonicalizeFilename(args.filename);
    if (!canonical) {
      return { content: [{ type: 'text', text: 'Error: filename canonicalized to empty string.' }] };
    }
    if (canonical.includes('/') || canonical.includes('\\')) {
      return { content: [{ type: 'text', text: 'Error: filename must not contain path separators.' }] };
    }

    let absPath: string;
    try {
      absPath = safeResolve(ctx.dataDir, `sources/${canonical}`);
    } catch (e) {
      if (e instanceof PathTraversalError) {
        return { content: [{ type: 'text', text: e.message }] };
      }
      throw e;
    }
    await mkdir(safeResolve(ctx.dataDir, 'sources'), { recursive: true });

    if (await fileExists(absPath)) {
      return {
        content: [
          {
            type: 'text',
            text: `Error: source already exists at sources/${canonical} (immutable invariant). Use a different filename.`,
          },
        ],
      };
    }

    if (args.content !== undefined) {
      await writeFile(absPath, args.content, 'utf-8');
    } else {
      const buf = Buffer.from(args.content_base64!, 'base64');
      await writeFile(absPath, buf);
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ ok: true, path: `sources/${canonical}`, original_filename: args.filename }, null, 2),
        },
      ],
    };
  },
};
