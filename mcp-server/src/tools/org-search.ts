/**
 * org_search — text search across nodes.
 *
 * Substring + token match against frontmatter (id/title/description) and body.
 * Returns ranked hits with snippets. No semantic search yet — that comes later.
 */

import { z } from 'zod';
import { walkNodes, nodeType, nodeTitle, type NodeFile } from '../lib/walk.js';
import type { ToolDefinition } from '../server.js';

const inputSchema = {
  type: 'object',
  properties: {
    query: { type: 'string', description: 'Search terms (case-insensitive, multi-token)' },
    type: {
      type: 'string',
      description: 'Optional filter by node type: unit, person, role, activity, stakeholder, commitment, language-term, identity, play',
    },
    limit: { type: 'number', description: 'Max results (default 20)' },
  },
  required: ['query'],
} as const;

const ArgsSchema = z.object({
  query: z.string().min(1),
  type: z.string().optional(),
  limit: z.number().int().positive().max(100).optional(),
});

interface Hit {
  id: string;
  path: string;
  type: string;
  title: string;
  score: number;
  snippet: string;
}

function tokenize(s: string): string[] {
  return s
    .toLowerCase()
    .split(/[\s,.;:()\[\]{}"'/\\—–-]+/)
    .filter((t) => t.length >= 2);
}

function scoreNode(node: NodeFile, tokens: string[]): { score: number; snippet: string } {
  const fm = node.frontmatter;
  const title = nodeTitle(node).toLowerCase();
  const description = (typeof fm.description === 'string' ? fm.description : '').toLowerCase();
  const id = node.id.toLowerCase();
  const body = node.body.toLowerCase();

  let score = 0;
  for (const tok of tokens) {
    if (id === tok) score += 10;
    else if (id.includes(tok)) score += 4;
    if (title.includes(tok)) score += 6;
    if (description.includes(tok)) score += 5;
    if (body.includes(tok)) score += 1;
  }

  // build snippet around first body match
  let snippet = '';
  for (const tok of tokens) {
    const idx = body.indexOf(tok);
    if (idx >= 0) {
      const start = Math.max(0, idx - 60);
      const end = Math.min(body.length, idx + tok.length + 60);
      snippet = (start > 0 ? '…' : '') + node.body.slice(start, end).replace(/\s+/g, ' ').trim() + (end < body.length ? '…' : '');
      break;
    }
  }
  if (!snippet) snippet = node.body.split('\n').find((l) => l.trim())?.slice(0, 140) ?? '';

  return { score, snippet };
}

export const orgSearchTool: ToolDefinition = {
  name: 'org_search',
  description:
    'Text search across all org/ nodes. Matches frontmatter (id, title, description) and body. Returns ranked hits with snippets. Use this before org_read when you do not know the exact node id, or to find all nodes touching a topic.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { query, type, limit = 20 } = ArgsSchema.parse(rawArgs);
    const tokens = tokenize(query);
    if (tokens.length === 0) {
      return { content: [{ type: 'text', text: 'Query too short — provide at least one token of length ≥2.' }] };
    }

    const all = await walkNodes(ctx.dataDir);
    const filtered = type ? all.filter((n) => nodeType(n) === type) : all;

    const hits: Hit[] = [];
    for (const node of filtered) {
      const { score, snippet } = scoreNode(node, tokens);
      if (score > 0) {
        hits.push({
          id: node.id,
          path: node.relPath,
          type: nodeType(node),
          title: nodeTitle(node),
          score,
          snippet,
        });
      }
    }

    hits.sort((a, b) => b.score - a.score);
    const top = hits.slice(0, limit);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ query, total: hits.length, returned: top.length, hits: top }, null, 2),
        },
      ],
    };
  },
};
