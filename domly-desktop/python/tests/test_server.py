import json
import pytest
from sidecar.server import DomlyServer

@pytest.mark.asyncio
async def test_dispatches_registered_handler():
    server = DomlyServer()
    received = []

    async def handler(payload):
        received.append(payload)

    server.on("set_credentials", handler)
    await server._dispatch({"type": "set_credentials", "sr_email": "a@b.com", "sr_password": "pw"})

    assert received == [{"type": "set_credentials", "sr_email": "a@b.com", "sr_password": "pw"}]

@pytest.mark.asyncio
async def test_unregistered_message_type_does_not_raise():
    server = DomlyServer()
    await server._dispatch({"type": "unknown_type"})

@pytest.mark.asyncio
async def test_broadcast_with_no_clients_does_not_raise():
    server = DomlyServer()
    await server.broadcast({"type": "status", "state": "idle"})
