/**
 * Path containment helper.
 *
 * Resolves a user-provided relative path against dataDir and verifies that
 * the resolved absolute path is INSIDE dataDir (no path traversal).
 *
 * Returns the absolute path on success, throws on violation.
 */

import { resolve, sep } from 'node:path';

export class PathTraversalError extends Error {
  constructor(input: string) {
    super(`Path traversal rejected: "${input}" resolves outside the data directory.`);
    this.name = 'PathTraversalError';
  }
}

/**
 * Resolve `relPath` against `dataDir` and verify containment.
 *
 * Containment rule: the resolved absolute path must equal `dataDir` or
 * start with `dataDir + sep`. Any `..` segments that would escape are blocked.
 */
export function safeResolve(dataDir: string, relPath: string): string {
  // Normalize dataDir without trailing separator
  const baseAbs = resolve(dataDir);
  const candidateAbs = resolve(baseAbs, relPath);
  const baseWithSep = baseAbs.endsWith(sep) ? baseAbs : baseAbs + sep;

  if (candidateAbs !== baseAbs && !candidateAbs.startsWith(baseWithSep)) {
    throw new PathTraversalError(relPath);
  }
  return candidateAbs;
}
