/**
 * org_skill_read — read the full SKILL.md body for a given skill.
 *
 * Pairs with org_skills_list (which is the index, name + description only).
 * Resolves both top-level skills (`skills/<name>/SKILL.md`) and nested
 * playbooks (`skills/playbooks/<name>/SKILL.md`).
 */

import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import matter from 'gray-matter';
import { z } from 'zod';

import type { ToolDefinition } from '../server.js';
import { safeResolve, PathTraversalError } from '../lib/safe-path.js';

const inputSchema = {
  type: 'object',
  properties: {
    name: {
      type: 'string',
      description:
        'Skill name (e.g., "ingest", "lint", "ai-exposure", "world-model", "new-playbook") or one of the cross-cutting docs ("CAPABILITIES", "STYLE", "ROADMAP"). Resolves to skills/<name>/SKILL.md, skills/playbooks/<name>/SKILL.md, or the top-level skills/<name>.md.',
    },
  },
  required: ['name'],
} as const;

const ArgsSchema = z.object({ name: z.string().min(1) });

export const orgSkillReadTool: ToolDefinition = {
  name: 'org_skill_read',
  description:
    'Read the full SKILL.md content (frontmatter + body) for a given skill name. Use this whenever you need to follow a skill recipe end to end — org_skills_list only returns the index. Returns { path, frontmatter, body }.',
  inputSchema,
  handler: async (rawArgs, ctx) => {
    const { name } = ArgsSchema.parse(rawArgs);
    const repoRoot = dirname(ctx.dataDir);
    const skillsRoot = resolve(repoRoot, 'skills');

    // Top-level cross-cutting docs in skills/ (CAPABILITIES, STYLE, ROADMAP)
    // are referenced by every playbook recipe but live next to the skill
    // folders rather than inside one. Resolve those by their bare upper-case
    // name as well as their .md filename.
    const candidates = [
      `${name}/SKILL.md`,
      `playbooks/${name}/SKILL.md`,
      `${name}.md`,
      `${name.toUpperCase()}.md`,
    ];

    let foundPath: string | null = null;
    for (const rel of candidates) {
      let abs: string;
      try {
        abs = safeResolve(skillsRoot, rel);
      } catch (e) {
        if (e instanceof PathTraversalError) continue;
        throw e;
      }
      try {
        await readFile(abs);
        foundPath = abs;
        break;
      } catch {
        // try next candidate
      }
    }

    if (!foundPath) {
      return {
        content: [
          {
            type: 'text',
            text: `Skill not found: "${name}". Use org_skills_list to discover available skills.`,
          },
        ],
      };
    }

    const raw = await readFile(foundPath, 'utf-8');
    const parsed = matter(raw);
    const result = {
      path: foundPath.replace(repoRoot + '/', ''),
      frontmatter: parsed.data,
      body: parsed.content.trim(),
    };

    return {
      content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
    };
  },
};
