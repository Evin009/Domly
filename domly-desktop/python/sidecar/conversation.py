import asyncio


class ConversationManager:
    def __init__(
        self,
        verify_voice_fn,
        record_command_fn,
        transcribe_fn,
        ask_claude_fn,
        speak_fn,
        enrolled_embedding: bytes,
        conversation_window_seconds: float = 8.0,
    ):
        self.verify_voice_fn = verify_voice_fn
        self.record_command_fn = record_command_fn
        self.transcribe_fn = transcribe_fn
        self.ask_claude_fn = ask_claude_fn
        self.speak_fn = speak_fn
        self.enrolled_embedding = enrolled_embedding
        self.conversation_window_seconds = conversation_window_seconds

    async def handle_command(self, server) -> None:
        await server.broadcast({"type": "status", "state": "listening"})
        command_audio = self.record_command_fn()

        if not self.verify_voice_fn(command_audio, self.enrolled_embedding):
            await server.broadcast({"type": "voice_rejected"})
            await server.broadcast({"type": "status", "state": "idle"})
            return

        try:
            await server.broadcast({"type": "status", "state": "processing"})
            text = self.transcribe_fn(command_audio)
            await server.broadcast({"type": "conversation_event", "role": "user", "text": text})

            response = await self.ask_claude_fn(text)
            await server.broadcast({"type": "conversation_event", "role": "assistant", "text": response})

            await server.broadcast({"type": "status", "state": "speaking"})
            self.speak_fn(response)
        except Exception as e:
            await server.broadcast({"type": "error", "message": str(e)})

        await server.broadcast({"type": "status", "state": "idle"})

    async def run_main_loop(self, server, wake_word_detector) -> None:
        while True:
            await server.broadcast({"type": "status", "state": "idle"})
            await asyncio.get_event_loop().run_in_executor(None, wake_word_detector.listen_for_wake_word)

            await self.handle_command(server)

            conversation_active = True
            while conversation_active:
                try:
                    await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(None, self.record_command_fn),
                        timeout=self.conversation_window_seconds,
                    )
                    await self.handle_command(server)
                except asyncio.TimeoutError:
                    conversation_active = False
