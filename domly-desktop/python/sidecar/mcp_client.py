from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sidecar import storage


@asynccontextmanager
async def smartrent_mcp_session():
    credentials = storage.load_credentials()
    if not credentials:
        raise ValueError("No SmartRent credentials cached — user must log in first")

    server_params = StdioServerParameters(
        command="uvx",
        args=["smartrent-mcp"],
        env={
            "SMARTRENT_EMAIL": credentials["sr_email"],
            "SMARTRENT_PASSWORD": credentials["sr_password"],
        },
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def mcp_tools_to_claude_format(mcp_tools: list) -> list[dict]:
    claude_tools = []
    for tool in mcp_tools:
        claude_tools.append({
            "name": tool.name,
            "description": tool.description or "",
            "input_schema": tool.inputSchema,
        })
    return claude_tools
