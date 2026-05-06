/**
 * org_neighbors — graph neighbors of a node up to N hops.
 *
 * Edges come from frontmatter fields that reference other node ids
 * (per AGENTS.md schema), plus reverse edges (who points back to this node).
 */

import { z } from 'zod';
import { walkNodes, nodeType, nodeTitle, type NodeFile } from '../lib/walk.js';
import type { ToolDefinition } from '../server.js';

const inputSchema = {
  type: 'object',
  properties: {
    id: { type: 'string', description: 'Starting node id (kebab-case)' },
    depth: { type: 'number', description: 'Hop depth (default 1, max 3)' },
  },
  required: ['id'],
} as const;

const ArgsSchema = z.object({
  id: z.string(),
  depth: z.number().int().positive().max(3).optional(),
});

// Frontmatter fields that reference node ids per current AGENTS.md schema.
const EDGE_FIELDS = [
  // unit
  'parent',
  'head_role',
  // person
  'role',
  'unit',
  // role
  'reports_to',
  // activity
  'performer',
  // commitment
  'parties_committing',
  'parties_benefiting',
  // language-term
  'related',
  // common
  'sources',
  'authority_basis',
] as const;

function extractRefs(node: NodeFile): { field: string; ref: string }[] {
  const out: { field: string; ref: string }[] = [];
  for (const f of EDGE_FIELDS) {
    const v = node.frontmatter[f];
    if (typeof v === 'string') out.push({ field: f, ref: normalizeRef(v) });
    else if (Array.isArray(v)) for (const item of v) if (typeof item === 'string') out.push({ field: f, ref: normalizeRef(item) });
  }
  return out;
}

function normalizeRef(ref: string): string {
  // strip file extension and leading paths (frontmatter ids are bare slugs)
  let r = ref.trim();
  r = r.replace(/\.md$/, '');
  r = r.split('/').pop() ?? r;
  return r;
}

interface NeighborRef {
  id: string;
  path?: string;
  type?: string;
  title?: string;
  via: string[];
  hop: number;
  resolved: boolean;
}

export const orgNeighborsTool: ToolDefinition = {
  name: 'org_neighbors',
  description:
    'Return the graph neighborhood of a node: outgoing references in frontmatter (parent, head_role, role, unit, performer, parties_committing, parties_benefiting, related, sources, authority_basis, reports_to) plus reverse edges (who points back). Set depth=2 or 3 for transitive expansion. Unresolved refs are returned with resolved=false.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { id, depth = 1 } = ArgsSchema.parse(rawArgs);
    const all = await walkNodes(ctx.dataDir);
    const byId = new Map<string, NodeFile>();
    for (const n of all) byId.set(n.id, n);

    const start = byId.get(id);
    if (!start) {
      return { content: [{ type: 'text', text: `Node not found: "${id}". Try org_search or org_list.` }] };
    }

    // BFS outwards
    const visited = new Map<string, NeighborRef>();
    const queue: { node: NodeFile; hop: number; via: string[] }[] = [
      { node: start, hop: 0, via: [] },
    ];
    visited.set(start.id, {
      id: start.id,
      path: start.relPath,
      type: nodeType(start),
      title: nodeTitle(start),
      via: [],
      hop: 0,
      resolved: true,
    });

    while (queue.length) {
      const { node, hop } = queue.shift()!;
      if (hop >= depth) continue;
      for (const { field, ref } of extractRefs(node)) {
        const target = byId.get(ref);
        if (visited.has(ref)) {
          const existing = visited.get(ref)!;
          if (!existing.via.includes(field)) existing.via.push(field);
          continue;
        }
        if (target) {
          visited.set(ref, {
            id: ref,
            path: target.relPath,
            type: nodeType(target),
            title: nodeTitle(target),
            via: [field],
            hop: hop + 1,
            resolved: true,
          });
          queue.push({ node: target, hop: hop + 1, via: [field] });
        } else {
          visited.set(ref, {
            id: ref,
            via: [field],
            hop: hop + 1,
            resolved: false,
          });
        }
      }
    }

    // reverse edges: anyone pointing to id (only from start, depth 1 reverse)
    const reverse: NeighborRef[] = [];
    for (const n of all) {
      if (n.id === id) continue;
      for (const { field, ref } of extractRefs(n)) {
        if (ref === id) {
          reverse.push({
            id: n.id,
            path: n.relPath,
            type: nodeType(n),
            title: nodeTitle(n),
            via: [`reverse:${field}`],
            hop: 1,
            resolved: true,
          });
          break;
        }
      }
    }

    const neighbors = Array.from(visited.values()).filter((n) => n.id !== id);
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            {
              start: { id: start.id, path: start.relPath, title: nodeTitle(start), type: nodeType(start) },
              depth,
              neighbors,
              reverse,
            },
            null,
            2
          ),
        },
      ],
    };
  },
};
