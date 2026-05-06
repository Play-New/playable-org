/**
 * org_skills_list — list workflow skills available alongside the org bundle.
 *
 * Skills are recipes that compose the mcp tools. They live in `<repo>/skills/<name>/SKILL.md`
 * (NOT inside org/). This tool walks the skills/ directory adjacent to the dataDir
 * and returns the metadata of each SKILL.md (name, description from frontmatter).
 *
 * Pairs with the built-in MCP `tools/list` method:
 * - `tools/list` enumerates the mcp primitives (org_read, org_write_node, ...)
 * - `org_skills_list` enumerates the workflow recipes (ingest, lint, ...)
 */

import { readFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import matter from 'gray-matter';
import fastGlob from 'fast-glob';

import type { ToolDefinition } from '../server.js';

const inputSchema = {
  type: 'object',
  properties: {},
} as const;

interface SkillEntry {
  name: string;
  description: string;
  path: string;
}

export const orgSkillsListTool: ToolDefinition = {
  name: 'org_skills_list',
  description:
    'List workflow skills available alongside org/. Skills are recipes (markdown files in <repo>/skills/<name>/SKILL.md) that compose the mcp primitives. Use this together with the built-in tools/list to know both what primitives and what workflows are available.',
  inputSchema,
  handler: async (_rawArgs, ctx) => {
    // skills/ lives at the repo root, sibling to org/
    const repoRoot = dirname(ctx.dataDir);
    const skillsRoot = resolve(repoRoot, 'skills');

    // Top-level skills (`skills/<name>/SKILL.md`) plus nested playbooks
    // (`skills/playbooks/<name>/SKILL.md`). Two distinct depths.
    const files = await fastGlob(['*/SKILL.md', 'playbooks/*/SKILL.md'], {
      cwd: skillsRoot,
      absolute: true,
    });
    const entries: SkillEntry[] = [];

    for (const f of files) {
      try {
        const raw = await readFile(f, 'utf-8');
        const parsed = matter(raw);
        const fm = parsed.data as Record<string, unknown>;
        const name = typeof fm.name === 'string' ? fm.name : '';
        const description = typeof fm.description === 'string' ? fm.description : '';
        if (name) {
          entries.push({
            name,
            description,
            path: f.replace(repoRoot + '/', ''),
          });
        }
      } catch {
        // skip unreadable
      }
    }

    entries.sort((a, b) => a.name.localeCompare(b.name));

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(
            { total: entries.length, skills: entries },
            null,
            2
          ),
        },
      ],
    };
  },
};
