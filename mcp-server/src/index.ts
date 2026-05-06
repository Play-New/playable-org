#!/usr/bin/env node
/**
 * MCP server entry point.
 * Exposes an Org folder as tools to MCP-compatible clients (Claude Desktop, Claude Code).
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { resolve } from 'node:path';
import { existsSync } from 'node:fs';

import { registerTools } from './server.js';

function parseArgs(argv: string[]): { dataDir: string } {
  const args = argv.slice(2);
  let dataDir = '';
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--data-dir' || args[i] === '-d') {
      dataDir = args[i + 1];
      i++;
    }
  }
  if (!dataDir) {
    console.error('Usage: playable-org-mcp --data-dir <path-to-Org-folder>');
    process.exit(1);
  }
  const resolved = resolve(dataDir);
  if (!existsSync(resolved)) {
    console.error(`Data dir not found: ${resolved}`);
    process.exit(1);
  }
  return { dataDir: resolved };
}

async function main() {
  const { dataDir } = parseArgs(process.argv);

  const server = new Server(
    {
      name: 'playable-org-mcp',
      version: '0.1.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  registerTools(server, { dataDir });

  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error(`[playable-org-mcp] connected, data-dir=${dataDir}`);
}

main().catch((err) => {
  console.error('[playable-org-mcp] fatal:', err);
  process.exit(1);
});
