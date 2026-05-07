/**
 * Find the repo root by walking up from a dataDir.
 *
 * Several mcp tools (org_lint_run, org_play_run, org_autoresearch_run)
 * spawn python scripts that live in the repo's `skills/` tree. They
 * need an absolute path to those scripts. The dataDir the agent passes
 * can be deep inside the repo (e.g. mcp-server/test-fixtures/sample-org)
 * — `dirname(dataDir)` is not always the repo root.
 *
 * This helper walks up the path looking for a directory containing
 * `skills/`. If none is found within 8 levels, it falls back to
 * `dirname(dataDir)` so the original behaviour is preserved for
 * direct-child dataDirs (the canonical case is dataDir = /repo/org/).
 */

import { dirname, resolve } from 'node:path';
import { stat } from 'node:fs/promises';

export async function findRepoRoot(dataDir: string): Promise<string> {
  let dir = resolve(dataDir);
  for (let i = 0; i < 8; i++) {
    try {
      const s = await stat(resolve(dir, 'skills'));
      if (s.isDirectory()) return dir;
    } catch {
      // not here, keep walking
    }
    const parent = dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return dirname(dataDir);
}
