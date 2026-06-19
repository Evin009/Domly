import json
import asyncio
import websockets

class DomlyServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        # Maps message 'type' string -> the async fn that handles it
        self._handlers: dict[str, callable] = {}
        
        # Tracks every currently-connected electrons client
        self._clients: set = set()
        
    # Registers a handler fn for a given message type    
    def on(self, message_type:str, handler) -> None:
        self._handlers[message_type] = handler
    
    # Looks up the right handler for this message and calls it
    # if no handler is registered for this type, does nothing
    async def _dispatch(self, payload: dict) -> None:
        handler = self._handlers.get(payload.get("type"))
        if handler:
            await handler(payload)
        
    # sends a message to every connected client
    # if nobody connected - does nothing    
    async def broadcast(self, message: dict) -> None:
        if not self._clients:
            return
        data = json.dumps(message)
        await asyncio.gather(*[client.send(data) for client in self._clients], return_exceptions=True)
        
    # calling automatically once per Electron client that connects
    # keeps running for as long as that client stays connected    
    async def _connection_handler(self, websocket) -> None:
        self._clients.add(websocket)
        try:
            async for raw_message in websocket:
                payload = json.loads(raw_message)
                await self._dispatch(payload)
        finally:
            self._clients.discard(websocket)
    
    
    # Starts the actual server and keeps it running forever
    async def start(self) -> None:
        async with websockets.serve(self._connection_handler, self.host, self.port):
            await asyncio.Future()
        

          
        
