import pytest


class FakeTool:
    def __init__(self, name, description, inputSchema):
        self.name = name
        self.description = description
        self.inputSchema = inputSchema


def test_mcp_tools_to_claude_format_converts_tool_shape():
    from sidecar.mcp_client import mcp_tools_to_claude_format

    tools = [FakeTool("get_status", "Get device status", {"type": "object", "properties": {}})]
    result = mcp_tools_to_claude_format(tools)

    assert result == [{
        "name": "get_status",
        "description": "Get device status",
        "input_schema": {"type": "object", "properties": {}},
    }]


@pytest.mark.asyncio
async def test_session_raises_without_credentials(monkeypatch):
    from sidecar import mcp_client

    monkeypatch.setattr(mcp_client.storage, "load_credentials", lambda: None)

    with pytest.raises(ValueError):
        async with mcp_client.smartrent_mcp_session():
            pass
