/**
 * org_list — list nodes by type and/or path prefix.
 *
 * Returns shallow listing (id, path, title, type, status) — not the body.
 * Use this to discover what exists; pair with org_read for content.
 */

import { z } from 'zod';
import { walkNodes, nodeType, nodeTitle } from '../lib/walk.js';
import type { ToolDefinition } from '../server.js';

const inputSchema = {
  type: 'object',
  properties: {
    type: {
      type: 'string',
      description: 'Filter by node type: unit, person, role, activity, stakeholder, commitment, language-term, identity, play',
    },
    path: {
      type: 'string',
      description: 'Filter by path prefix relative to dataDir, e.g., "nodes/people" or "commitments"',
    },
    limit: { type: 'number', description: 'Max results (default 200)' },
  },
} as const;

const ArgsSchema = z.object({
  type: z.string().optional(),
  path: z.string().optional(),
  limit: z.number().int().positive().max(1000).optional(),
});

export const orgListTool: ToolDefinition = {
  name: 'org_list',
  description:
    'List Org/ nodes filtered by type or path prefix. Returns shallow metadata (id, path, title, type) without body. Use to discover what exists before drilling in with org_read.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { type, path, limit = 200 } = ArgsSchema.parse(rawArgs);
    const all = await walkNodes(ctx.dataDir);

    let filtered = all;
    if (type) filtered = filtered.filter((n) => nodeType(n) === type);
    if (path) {
      const prefix = path.replace(/\\/g, '/').replace(/\/$/, '') + '/';
      filtered = filtered.filter((n) => n.relPath.startsWith(prefix) || n.relPath === path);
    }

    const items = filtered.slice(0, limit).map((n) => ({
      id: n.id,
      path: n.relPath,
      type: nodeType(n),
      title: nodeTitle(n),
    }));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify({ total: filtered.length, returned: items.length, items }, null, 2),
        },
      ],
    };
  },
};
