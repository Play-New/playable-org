/**
 * Filesystem helpers for walking the org folder and parsing frontmatter.
 */

import { readFile } from 'node:fs/promises';
import { relative } from 'node:path';
import matter from 'gray-matter';
import fastGlob from 'fast-glob';

export interface NodeFile {
  /** absolute path on disk */
  absPath: string;
  /** path relative to dataDir, with forward slashes */
  relPath: string;
  /** bare filename without .md, e.g. "personale" */
  id: string;
  /** parsed frontmatter (object) */
  frontmatter: Record<string, unknown>;
  /** body text (after frontmatter) */
  body: string;
}

const NODE_PATTERNS = [
  'nodes/**/*.md',
  'identity/*.md',
  'language/*.md',
  'commitments/*.md',
  'financials/*.md',
  'plays/**/*.md',
];

const IGNORE_PATTERNS = [
  '**/README.md',
  '**/_*.md',
  '**/SKILL.md',
];

export async function walkNodes(dataDir: string): Promise<NodeFile[]> {
  const files = await fastGlob(NODE_PATTERNS, {
    cwd: dataDir,
    absolute: true,
    ignore: IGNORE_PATTERNS,
  });

  const out: NodeFile[] = [];
  for (const absPath of files) {
    try {
      const raw = await readFile(absPath, 'utf-8');
      const parsed = matter(raw);
      const relPath = relative(dataDir, absPath).split('\\').join('/');
      const id = relPath.replace(/^.*\//, '').replace(/\.md$/, '');
      out.push({
        absPath,
        relPath,
        id,
        frontmatter: parsed.data as Record<string, unknown>,
        body: parsed.content,
      });
    } catch {
      // skip unreadable files
    }
  }
  return out;
}

export function nodeType(node: NodeFile): string {
  const fm = node.frontmatter;
  if (typeof fm.type === 'string') return fm.type;
  // infer from path
  const segs = node.relPath.split('/');
  if (segs[0] === 'nodes' && segs.length >= 3) return segs[1].replace(/s$/, '');
  if (segs[0] === 'identity') return 'identity';
  if (segs[0] === 'language') return 'language-term';
  if (segs[0] === 'commitments') return 'commitment';
  if (segs[0] === 'financials') return 'financial-summary';
  if (segs[0] === 'plays') return 'play';
  return 'unknown';
}

export function nodeTitle(node: NodeFile): string {
  const fm = node.frontmatter;
  if (typeof fm.title === 'string') return fm.title;
  if (typeof fm.name === 'string') return fm.name;
  // first H1 in body
  const m = node.body.match(/^#\s+(.+)$/m);
  if (m) return m[1].trim();
  return node.id;
}
