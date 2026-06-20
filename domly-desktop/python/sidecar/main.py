import asyncio
import base64
from sidecar.server import DomlyServer
from sidecar.wake_word import WakeWordDetector
from sidecar.vad import record_until_silence
from sidecar.voice_auth import verify_voice, enroll_voice
from sidecar.stt import transcribe
from sidecar.claude_orchestrator import ask_claude
from sidecar.tts import speak
from sidecar.conversation import ConversationManager
from sidecar import storage


async def handle_set_credentials(payload: dict) -> None:
    storage.save_credentials(payload["sr_email"], payload["sr_password"])


def make_enroll_handlers(server: DomlyServer):
    samples: list[bytes] = []

    async def handle_enroll_start(payload: dict) -> None:
        samples.clear()

    async def handle_enroll_sample(payload: dict) -> None:
        samples.append(base64.b64decode(payload["audio"]))
        if len(samples) >= 3:
            enroll_voice(samples)
            await server.broadcast({"type": "enrollment_complete", "success": True})

    return handle_enroll_start, handle_enroll_sample


async def main() -> None:
    server = DomlyServer()

    async def handle_quit(payload: dict) -> None:
        raise SystemExit(0)

    server.on("set_credentials", handle_set_credentials)
    enroll_start, enroll_sample = make_enroll_handlers(server)
    server.on("enroll_voice_start", enroll_start)
    server.on("enroll_voice_sample", enroll_sample)
    server.on("quit", handle_quit)

    server_task = asyncio.create_task(server.start())

    if not storage.has_credentials() or not storage.has_voice_embedding():
        print("Waiting for login and voice enrollment via Electron UI...")
        while not storage.has_credentials() or not storage.has_voice_embedding():
            await asyncio.sleep(1)

    enrolled_embedding = storage.load_voice_embedding()
    detector = WakeWordDetector(keyword="hey_jarvis")

    manager = ConversationManager(
        verify_voice_fn=verify_voice,
        record_command_fn=record_until_silence,
        transcribe_fn=transcribe,
        ask_claude_fn=ask_claude,
        speak_fn=speak,
        enrolled_embedding=enrolled_embedding,
    )

    await asyncio.gather(server_task, manager.run_main_loop(server, detector))


if __name__ == "__main__":
    asyncio.run(main())
