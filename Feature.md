# Python Sidecar — Tech Stack Breakdown

Reference for every library used in the `domly-desktop/python` sidecar, grouped by what it does. See the [implementation plan](docs/superpowers/plans/2026-06-16-python-sidecar.md) for how each one is actually used task-by-task.

## Communication (talks to Electron)

- **`websockets`** — lets the Python process run a server that Electron connects to, so both sides can send real-time JSON messages back and forth

## Audio I/O (hardware)

- **`sounddevice`** — records from the mic and plays through speakers
- **`numpy`** — audio comes in as raw numbers (a waveform); numpy is how Python manipulates that array of numbers efficiently
- **`pyaudio`** — a second audio library, specifically required by Porcupine for its low-level streaming format

## Wake Word Detection

- **`pvporcupine`** — Picovoice's wake word engine. Runs entirely locally, constantly listens to short audio chunks, and signals the instant it hears the trigger phrase

## Voice Authentication

- **`resemblyzer`** — generates a "voice embedding" (a list of numbers that mathematically represents how a voice sounds). Embeddings are compared to verify if a new voice matches the enrolled one

## Speech-to-Text

- **`openai`** — official OpenAI Python SDK, used here just to call the Whisper API (audio → text)

## The "Brain"

- **`anthropic`** — official Claude API SDK, sends transcribed text to Claude
- **`mcp`** — same MCP SDK used to build `smartrent-mcp`. Here it's used as a **client** instead of a server — it spawns `smartrent-mcp` as a subprocess and lets Claude call its tools

## Text-to-Speech

- **`elevenlabs`** — converts Claude's text response into spoken audio

## Storage & Security

- **`cryptography`** — Fernet encryption (same pattern as `smartrent-mcp`), encrypts cached credentials and the voice embedding on disk
- **`python-dotenv`** — loads API keys from `.env`, same pattern as `smartrent-mcp`

## Testing

- **`pytest`** + **`pytest-asyncio`** — `pytest-asyncio` specifically lets tests cover `async def` functions, since most of this project is async (waiting on network/audio I/O)

---

## Complexity Ranking (easiest → hardest)

1. Storage encryption — already done once in `smartrent-mcp`
2. WebSocket server — new, but a straightforward pattern
3. Audio recording/playback — new, mostly just calling functions
4. Whisper/Claude/ElevenLabs API calls — similar shape to API calls already done before
5. Wake word + voice embeddings — genuinely new ML concepts, explained in depth when reached in the plan
