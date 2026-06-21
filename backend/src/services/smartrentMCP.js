import { Client } from '@modelcontextprotocol/sdk/client/index.js'
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js'
import Anthropic from '@anthropic-ai/sdk'

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY })
const MODEL = 'claude-sonnet-4-6'

// Spawns `smartrent-mcp` (pip-installed) as a subprocess, runs fn, then closes.
async function withMCPSession(sr_email, sr_password, fn) {
  const transport = new StdioClientTransport({
    command: 'smartrent-mcp',
    env: {
      ...process.env,
      SMARTRENT_EMAIL: sr_email,
      SMARTRENT_PASSWORD: sr_password,
    }
  })

  const client = new Client({ name: 'domly-backend', version: '1.0.0' })
  await client.connect(transport)

  try {
    return await fn(client)
  } finally {
    await client.close()
  }
}

// Try to connect and list tools — if SmartRent rejects the creds, the process exits with error.
export async function validateCredentials(sr_email, sr_password) {
  try {
    await withMCPSession(sr_email, sr_password, (client) => client.listTools())
    return true
  } catch {
    return false
  }
}

// Natural language command → Claude picks the right MCP tool → returns response text.
export async function runCommand(sr_email, sr_password, commandText) {
  return withMCPSession(sr_email, sr_password, async (client) => {
    const { tools: mcpTools } = await client.listTools()

    // Convert MCP tool format → Claude tool format
    const claudeTools = mcpTools.map(t => ({
      name: t.name,
      description: t.description || '',
      input_schema: t.inputSchema,
    }))

    const messages = [{ role: 'user', content: commandText }]

    // Claude tool-calling loop
    while (true) {
      const response = await anthropic.messages.create({
        model: MODEL,
        max_tokens: 1024,
        tools: claudeTools,
        messages,
      })

      // No more tool calls — return Claude's final text answer
      if (response.stop_reason !== 'tool_use') {
        return response.content
          .filter(b => b.type === 'text')
          .map(b => b.text)
          .join('')
      }

      messages.push({ role: 'assistant', content: response.content })

      // Execute each tool call against the MCP server
      const toolResults = []
      for (const block of response.content) {
        if (block.type !== 'tool_use') continue
        const result = await client.callTool({ name: block.name, arguments: block.input })
        const resultText = result.content
          .filter(c => c.type === 'text')
          .map(c => c.text)
          .join('')
        toolResults.push({
          type: 'tool_result',
          tool_use_id: block.id,
          content: resultText,
        })
      }

      messages.push({ role: 'user', content: toolResults })
    }
  })
}
