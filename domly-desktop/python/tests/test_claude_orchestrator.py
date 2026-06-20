import pytest
from unittest.mock import AsyncMock, MagicMock


class FakeTextBlock:
    type = "text"
    def __init__(self, text):
        self.text = text


class FakeToolUseBlock:
    type = "tool_use"
    def __init__(self, name, input, id):
        self.name = name
        self.input = input
        self.id = id


class FakeResponse:
    def __init__(self, stop_reason, content):
        self.stop_reason = stop_reason
        self.content = content


class FakeResultContent:
    def __init__(self, text):
        self.text = text


@pytest.mark.asyncio
async def test_run_tool_loop_calls_tool_then_returns_final_text():
    from sidecar.claude_orchestrator import _run_tool_loop

    tool_call_response = FakeResponse(
        stop_reason="tool_use",
        content=[FakeToolUseBlock(name="get_status", input={}, id="tool_1")],
    )
    final_response = FakeResponse(
        stop_reason="end_turn",
        content=[FakeTextBlock("Lights are on")],
    )

    fake_client = MagicMock()
    fake_client.messages.create.side_effect = [tool_call_response, final_response]

    fake_session = MagicMock()
    fake_session.call_tool = AsyncMock(return_value=MagicMock(content=[FakeResultContent("status: on")]))

    result = await _run_tool_loop(fake_client, fake_session, claude_tools=[], user_text="status?")

    assert result == "Lights are on"
    fake_session.call_tool.assert_awaited_once_with("get_status", {})


@pytest.mark.asyncio
async def test_run_tool_loop_returns_immediately_with_no_tool_use():
    from sidecar.claude_orchestrator import _run_tool_loop

    final_response = FakeResponse(
        stop_reason="end_turn",
        content=[FakeTextBlock("Hello there")],
    )

    fake_client = MagicMock()
    fake_client.messages.create.return_value = final_response

    fake_session = MagicMock()
    fake_session.call_tool = AsyncMock()

    result = await _run_tool_loop(fake_client, fake_session, claude_tools=[], user_text="hi")

    assert result == "Hello there"
    fake_session.call_tool.assert_not_awaited()
