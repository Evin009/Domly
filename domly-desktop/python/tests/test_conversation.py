import pytest
from unittest.mock import AsyncMock, MagicMock
from sidecar.conversation import ConversationManager


@pytest.mark.asyncio
async def test_processes_one_command_and_broadcasts_status():
    server = MagicMock()
    server.broadcast = AsyncMock()

    manager = ConversationManager(
        verify_voice_fn=lambda audio, embedding: True,
        record_command_fn=lambda: b"fake_audio",
        transcribe_fn=lambda audio: "turn on the lights",
        ask_claude_fn=AsyncMock(return_value="Lights are on"),
        speak_fn=lambda text: None,
        enrolled_embedding=b"fake_embedding",
    )

    await manager.handle_command(server)

    statuses = [call.args[0]["state"] for call in server.broadcast.call_args_list if call.args[0]["type"] == "status"]
    assert "processing" in statuses
    assert "speaking" in statuses
    assert "idle" in statuses


@pytest.mark.asyncio
async def test_rejects_unverified_voice():
    server = MagicMock()
    server.broadcast = AsyncMock()

    manager = ConversationManager(
        verify_voice_fn=lambda audio, embedding: False,
        record_command_fn=lambda: b"fake_audio",
        transcribe_fn=lambda audio: "turn on the lights",
        ask_claude_fn=AsyncMock(),
        speak_fn=lambda text: None,
        enrolled_embedding=b"fake_embedding",
    )

    await manager.handle_command(server)

    types = [call.args[0]["type"] for call in server.broadcast.call_args_list]
    assert "voice_rejected" in types
    manager.ask_claude_fn.assert_not_called()


@pytest.mark.asyncio
async def test_broadcasts_error_when_ask_claude_fails():
    server = MagicMock()
    server.broadcast = AsyncMock()

    async def failing_ask_claude(text):
        raise RuntimeError("Claude API timeout")

    manager = ConversationManager(
        verify_voice_fn=lambda audio, embedding: True,
        record_command_fn=lambda: b"fake_audio",
        transcribe_fn=lambda audio: "turn on the lights",
        ask_claude_fn=failing_ask_claude,
        speak_fn=lambda text: None,
        enrolled_embedding=b"fake_embedding",
    )

    await manager.handle_command(server)

    error_calls = [call.args[0] for call in server.broadcast.call_args_list if call.args[0]["type"] == "error"]
    assert error_calls == [{"type": "error", "message": "Claude API timeout"}]

    statuses = [call.args[0]["state"] for call in server.broadcast.call_args_list if call.args[0]["type"] == "status"]
    assert statuses[-1] == "idle"


@pytest.mark.asyncio
async def test_broadcasts_error_when_speak_fails():
    server = MagicMock()
    server.broadcast = AsyncMock()

    def failing_speak(text):
        raise RuntimeError("ElevenLabs quota exceeded")

    manager = ConversationManager(
        verify_voice_fn=lambda audio, embedding: True,
        record_command_fn=lambda: b"fake_audio",
        transcribe_fn=lambda audio: "turn on the lights",
        ask_claude_fn=AsyncMock(return_value="Lights are on"),
        speak_fn=failing_speak,
        enrolled_embedding=b"fake_embedding",
    )

    await manager.handle_command(server)

    error_calls = [call.args[0] for call in server.broadcast.call_args_list if call.args[0]["type"] == "error"]
    assert error_calls == [{"type": "error", "message": "ElevenLabs quota exceeded"}]
