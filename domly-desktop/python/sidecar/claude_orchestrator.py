import os
from anthropic import Anthropic
from dotenv import load_dotenv
from sidecar.mcp_client import smartrent_mcp_session, mcp_tools_to_claude_format

load_dotenv()

_client = None
MODEL = "claude-haiku-4-5-20251001"


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def _run_tool_loop(client, session, claude_tools: list[dict], user_text: str) -> str:
    messages = [{"role": "user", "content": user_text}]

    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=claude_tools,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(block.text for block in response.content if block.type == "text")

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = await session.call_tool(block.name, block.input)
                result_text = "".join(c.text for c in result.content if hasattr(c, "text"))
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                })

        messages.append({"role": "user", "content": tool_results})


async def ask_claude(user_text: str) -> str:
    client = _get_client()
    async with smartrent_mcp_session() as session:
        tools_response = await session.list_tools()
        claude_tools = mcp_tools_to_claude_format(tools_response.tools)
        return await _run_tool_loop(client, session, claude_tools, user_text)
