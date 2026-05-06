/**
 * org_read — read a node's content + frontmatter by id.
 *
 * The id resolves to a markdown file in the org folder via:
 *   1. Direct path lookup if id contains "/" (e.g., "nodes/units/personale")
 *   2. Glob search if id is bare (e.g., "personale" → finds nodes/units/personale.md)
 */

import { readFile } from 'node:fs/promises';
import matter from 'gray-matter';
import fastGlob from 'fast-glob';
import { z } from 'zod';

import type { ToolDefinition } from '../server.js';
import { safeResolve, PathTraversalError } from '../lib/safe-path.js';

const inputSchema = {
  type: 'object',
  properties: {
    id: {
      type: 'string',
      description:
        'Node id (kebab-case, e.g., "personale", "rogledi") or relative path (e.g., "nodes/units/personale.md"). Bare ids are searched across nodes/, identity/, language/, commitments/, financials/, plays/. The root-level org docs ("log", "index", "AGENTS", "README", "open-questions") are also resolvable as bare ids.',
    },
  },
  required: ['id'],
} as const;

const ArgsSchema = z.object({ id: z.string() });

// Root-level org meta-docs: not nodes per se, but legitimate read targets.
const ROOT_DOCS = new Set(['log', 'index', 'AGENTS', 'README', 'open-questions']);

async function findNodeFile(dataDir: string, id: string): Promise<string | null> {
  // If id contains "/" treat as relative path with traversal containment
  if (id.includes('/')) {
    let candidate: string;
    try {
      candidate = safeResolve(dataDir, id.endsWith('.md') ? id : `${id}.md`);
    } catch (e) {
      if (e instanceof PathTraversalError) return null;
      throw e;
    }
    try {
      await readFile(candidate);
      return candidate;
    } catch {
      return null;
    }
  }

  // Bare id resolving to a root-level org doc
  if (ROOT_DOCS.has(id)) {
    let candidate: string;
    try {
      candidate = safeResolve(dataDir, `${id}.md`);
    } catch (e) {
      if (e instanceof PathTraversalError) return null;
      throw e;
    }
    try {
      await readFile(candidate);
      return candidate;
    } catch {
      return null;
    }
  }

  // Otherwise glob across the structured folders
  const patterns = [
    `nodes/**/${id}.md`,
    `identity/${id}.md`,
    `language/${id}.md`,
    `commitments/${id}.md`,
    `financials/${id}.md`,
    `plays/${id}.md`,
  ];

  const results = await fastGlob(patterns, { cwd: dataDir, absolute: true });
  return results[0] ?? null;
}

export const orgReadTool: ToolDefinition = {
  name: 'org_read',
  description:
    'Read a node\'s frontmatter and body by id. Returns YAML frontmatter parsed as JSON plus the markdown body. Use this to access any node in org/: units, people, roles, activities, stakeholders, language-terms, commitments, identity files, plays.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { id } = ArgsSchema.parse(rawArgs);
    const filePath = await findNodeFile(ctx.dataDir, id);

    if (!filePath) {
      return {
        content: [
          {
            type: 'text',
            text: `Node not found: "${id}". Try org_list or org_search to discover available nodes.`,
          },
        ],
      };
    }

    const raw = await readFile(filePath, 'utf-8');
    const parsed = matter(raw);

    const result = {
      path: filePath.replace(ctx.dataDir + '/', ''),
      frontmatter: parsed.data,
      body: parsed.content.trim(),
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  },
};
