/**
 * MCP server setup and tool registration.
 * Tools are loaded from src/tools/ and registered against the SDK Server.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { orgReadTool } from './tools/org-read.js';
import { orgSearchTool } from './tools/org-search.js';
import { orgListTool } from './tools/org-list.js';
import { orgNeighborsTool } from './tools/org-neighbors.js';
import { orgWriteNodeTool } from './tools/org-write-node.js';
import { orgSaveSourceTool } from './tools/org-save-source.js';
import { orgLogAppendTool } from './tools/org-log-append.js';
import { orgSkillsListTool } from './tools/org-skills-list.js';
import { orgSkillReadTool } from './tools/org-skill-read.js';
import { orgLintRunTool } from './tools/org-lint-run.js';
import { orgPlayRunTool } from './tools/org-play-run.js';
import { orgOpenTool } from './tools/org-open.js';

export interface Context {
  dataDir: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: object;
  handler: (args: unknown, ctx: Context) => Promise<{ content: Array<{ type: 'text'; text: string }> }>;
}

export function registerTools(server: Server, ctx: Context) {
  const tools: ToolDefinition[] = [
    orgReadTool,
    orgSearchTool,
    orgListTool,
    orgNeighborsTool,
    orgWriteNodeTool,
    orgSaveSourceTool,
    orgLogAppendTool,
    orgSkillsListTool,
    orgSkillReadTool,
    orgLintRunTool,
    orgPlayRunTool,
    orgOpenTool,
  ];

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: tools.map((t) => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema,
    })),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const tool = tools.find((t) => t.name === request.params.name);
    if (!tool) {
      throw new Error(`Unknown tool: ${request.params.name}`);
    }
    return await tool.handler(request.params.arguments ?? {}, ctx);
  });
}
