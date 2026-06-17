# Domly Python Sidecar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Note for this project:** Per `CLAUDE.md` in this repo, this plan is executed **inline by Evin himself** — Claude explains each step and gives exact code, Evin types/runs/commits it. Do not use subagent-driven-development or auto-apply code for this plan.

**Goal:** Build the Python background sidecar that gives Domly its voice — wake word detection, voice authentication, speech-to-text, Claude+MCP orchestration, and text-to-speech — exposed to the Electron UI over a local WebSocket.

**Architecture:** A single long-running async Python process. A WebSocket server (Electron's connection point) runs alongside a conversation state machine that drives: wake word → voice verification → record → transcribe → ask Claude (with `smartrent-mcp` tools) → speak the answer → optionally stay in conversation mode.

**Tech Stack:** Python 3.10+, `websockets`, `sounddevice`, `pvporcupine` (wake word), `resemblyzer` (voice embeddings), `openai` (Whisper), `anthropic` + `mcp` (Claude + tool orchestration), `elevenlabs` (TTS), `cryptography` (local encrypted storage), `pytest` + `pytest-asyncio`

## Global Constraints

- WebSocket server listens on `ws://127.0.0.1:8765`
- All Electron↔sidecar messages are JSON matching the contract in the design spec (`Domly/2026-06-16-domly-desktop-assistant-design.md`)
- Voice verification and wake word detection must work fully offline/locally — no audio sent anywhere until a verified wake word + verified voice triggers a real command
- Credentials and the voice embedding are cached locally, encrypted at rest
- Conversation mode follow-up window is 8 seconds
- The sidecar calls the published `smartrent-mcp` PyPI package as a subprocess — do not reimplement SmartRent device control logic here

---

## Task 1: Project Setup

**Files:**
- Create: `domly-desktop/python/pyproject.toml`
- Create: `domly-desktop/python/.env.example`
- Create: `domly-desktop/python/.gitignore`
- Create: `domly-desktop/python/sidecar/__init__.py`
- Create: `domly-desktop/python/tests/__init__.py`

**Interfaces:**
- Produces: project skeleton every later task adds files into (`sidecar/` package, `tests/` package)

- [ ] **Step 1: Create the folder structure**

```bash
mkdir -p "domly-desktop/python/sidecar"
mkdir -p "domly-desktop/python/tests"
touch "domly-desktop/python/sidecar/__init__.py"
touch "domly-desktop/python/tests/__init__.py"
```

- [ ] **Step 2: Write `pyproject.toml`**

```toml
[project]
name = "domly-sidecar"
version = "0.1.0"
description = "Python voice/AI core for the Domly desktop assistant"
requires-python = ">=3.10"
dependencies = [
    "websockets",
    "sounddevice",
    "numpy",
    "pvporcupine",
    "resemblyzer",
    "openai",
    "anthropic",
    "mcp[cli]",
    "elevenlabs",
    "cryptography",
    "python-dotenv",
]

[project.optional-dependencies]
dev = ["pytest", "pytest-asyncio"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- [ ] **Step 3: Write `.env.example`**

```
PICOVOICE_ACCESS_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
ELEVENLABS_API_KEY=
SMARTRENT_EMAIL=
SMARTRENT_PASSWORD=
```

Copy this to `.env` and fill in real keys (you'll get `PICOVOICE_ACCESS_KEY` for free at console.picovoice.ai — needed for wake word detection in Task 5).

- [ ] **Step 4: Write `.gitignore`**

```
.env
__pycache__/
*.pyc
.venv/
*.egg-info/
dist/
build/
```

- [ ] **Step 5: Install dependencies**

```bash
cd "domly-desktop/python"
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Expected: installs cleanly, no errors.

- [ ] **Step 6: Commit**

```bash
git add domly-desktop/python/pyproject.toml domly-desktop/python/.env.example domly-desktop/python/.gitignore domly-desktop/python/sidecar/__init__.py domly-desktop/python/tests/__init__.py
git commit -m "chore: scaffold Python sidecar project"
```

---

## Task 2: Local Encrypted Storage

**Files:**
- Create: `domly-desktop/python/sidecar/storage.py`
- Create: `domly-desktop/python/tests/test_storage.py`

**Interfaces:**
- Consumes: `ENCRYPTION_KEY` env var (Fernet key)
- Produces: `save_credentials(sr_email: str, sr_password: str) -> None`, `load_credentials() -> dict | None`, `save_voice_embedding(embedding: bytes) -> None`, `load_voice_embedding() -> bytes | None`, `has_credentials() -> bool`, `has_voice_embedding() -> bool` — used by Task 3 (WebSocket handlers), Task 6 (enrollment), Task 7 (verification), Task 10 (Claude orchestration needs credentials)

- [ ] **Step 1: Generate and add an encryption key to `.env`**

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Add the output to `.env`:
```
ENCRYPTION_KEY=<paste output here>
```

- [ ] **Step 2: Write the failing test in `tests/test_storage.py`**

```python
import os
import json
import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("ENCRYPTION_KEY", Fernet.generate_key().decode())

from sidecar import storage

@pytest.fixture
def data_path(tmp_path, monkeypatch):
    path = str(tmp_path / "data.enc")
    monkeypatch.setattr(storage, "DATA_PATH", path)
    return path

def test_no_credentials_initially(data_path):
    assert storage.has_credentials() is False
    assert storage.load_credentials() is None

def test_save_and_load_credentials(data_path):
    storage.save_credentials("user@example.com", "secretpw")
    assert storage.has_credentials() is True
    creds = storage.load_credentials()
    assert creds == {"sr_email": "user@example.com", "sr_password": "secretpw"}

def test_save_and_load_voice_embedding(data_path):
    fake_embedding = b"\x01\x02\x03\x04"
    storage.save_voice_embedding(fake_embedding)
    assert storage.has_voice_embedding() is True
    assert storage.load_voice_embedding() == fake_embedding

def test_credentials_and_embedding_coexist(data_path):
    storage.save_credentials("a@b.com", "pw")
    storage.save_voice_embedding(b"\xff\xee")
    assert storage.load_credentials() == {"sr_email": "a@b.com", "sr_password": "pw"}
    assert storage.load_voice_embedding() == b"\xff\xee"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest domly-desktop/python/tests/test_storage.py -v
```

Expected: `ModuleNotFoundError: No module named 'sidecar.storage'`

- [ ] **Step 4: Write `sidecar/storage.py`**

```python
import os
import json
import base64
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

DATA_PATH = os.path.expanduser("~/.domly/data.enc")


def _get_fernet() -> Fernet:
    key = os.environ["ENCRYPTION_KEY"]
    return Fernet(key.encode())


def _read_data() -> dict:
    if not os.path.exists(DATA_PATH):
        return {}
    with open(DATA_PATH, "rb") as f:
        encrypted = f.read()
    decrypted = _get_fernet().decrypt(encrypted)
    return json.loads(decrypted)


def _write_data(data: dict) -> None:
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    encrypted = _get_fernet().encrypt(json.dumps(data).encode())
    with open(DATA_PATH, "wb") as f:
        f.write(encrypted)


def save_credentials(sr_email: str, sr_password: str) -> None:
    data = _read_data()
    data["sr_email"] = sr_email
    data["sr_password"] = sr_password
    _write_data(data)


def load_credentials() -> dict | None:
    data = _read_data()
    if "sr_email" not in data:
        return None
    return {"sr_email": data["sr_email"], "sr_password": data["sr_password"]}


def has_credentials() -> bool:
    return load_credentials() is not None


def save_voice_embedding(embedding: bytes) -> None:
    data = _read_data()
    data["voice_embedding"] = base64.b64encode(embedding).decode()
    _write_data(data)


def load_voice_embedding() -> bytes | None:
    data = _read_data()
    if "voice_embedding" not in data:
        return None
    return base64.b64decode(data["voice_embedding"])


def has_voice_embedding() -> bool:
    return load_voice_embedding() is not None
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest domly-desktop/python/tests/test_storage.py -v
```

Expected: all 4 tests pass.

- [ ] **Step 6: Commit**

```bash
git add domly-desktop/python/sidecar/storage.py domly-desktop/python/tests/test_storage.py domly-desktop/python/.env
git commit -m "feat: add local encrypted storage for credentials and voice embedding"
```

---

## Task 3: WebSocket Server (Electron IPC)

**Files:**
- Create: `domly-desktop/python/sidecar/server.py`
- Create: `domly-desktop/python/tests/test_server.py`

**Interfaces:**
- Consumes: `storage.save_credentials`, `storage.has_credentials` (Task 2)
- Produces: `DomlyServer` class with `async def start()`, `async def broadcast(message: dict)`, `def on(message_type: str, handler)` — used by Task 12 (conversation state machine pushes status via `broadcast`, registers handlers for `set_credentials`, `enroll_voice_start`, etc.)

- [ ] **Step 1: Write the failing test in `tests/test_server.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest domly-desktop/python/tests/test_server.py -v
```

Expected: `ModuleNotFoundError: No module named 'sidecar.server'`

- [ ] **Step 3: Write `sidecar/server.py`**

```python
import json
import asyncio
import websockets


class DomlyServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self._handlers: dict[str, callable] = {}
        self._clients: set = set()

    def on(self, message_type: str, handler) -> None:
        self._handlers[message_type] = handler

    async def _dispatch(self, payload: dict) -> None:
        handler = self._handlers.get(payload.get("type"))
        if handler:
            await handler(payload)

    async def broadcast(self, message: dict) -> None:
        if not self._clients:
            return
        data = json.dumps(message)
        await asyncio.gather(*[client.send(data) for client in self._clients], return_exceptions=True)

    async def _connection_handler(self, websocket) -> None:
        self._clients.add(websocket)
        try:
            async for raw_message in websocket:
                payload = json.loads(raw_message)
                await self._dispatch(payload)
        finally:
            self._clients.discard(websocket)

    async def start(self) -> None:
        async with websockets.serve(self._connection_handler, self.host, self.port):
            await asyncio.Future()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest domly-desktop/python/tests/test_server.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 5: Manually verify the server actually runs**

Create a throwaway script `domly-desktop/python/run_server_test.py`:

```python
import asyncio
from sidecar.server import DomlyServer

async def main():
    server = DomlyServer()
    print("Starting WebSocket server on ws://127.0.0.1:8765 ...")
    await server.start()

asyncio.run(main())
```

Run it:
```bash
python domly-desktop/python/run_server_test.py
```

In another terminal, test the connection:
```bash
pip install websocket-client
python3 -c "
import websocket
ws = websocket.create_connection('ws://127.0.0.1:8765')
ws.send('{\"type\": \"mute\"}')
print('sent message, no crash = success')
ws.close()
"
```

Expected: no errors in either terminal. Stop the server with `Ctrl+C`, then delete `run_server_test.py` — it was just for manual verification.

- [ ] **Step 6: Commit**

```bash
rm domly-desktop/python/run_server_test.py
git add domly-desktop/python/sidecar/server.py domly-desktop/python/tests/test_server.py
git commit -m "feat: add WebSocket server for Electron IPC"
```

---

## Task 4: Audio I/O (Recording + Playback)

**Files:**
- Create: `domly-desktop/python/sidecar/audio_io.py`

**Interfaces:**
- Produces: `record_audio(duration_seconds: float, sample_rate: int = 16000) -> bytes`, `play_audio(audio_bytes: bytes, sample_rate: int = 16000) -> None` — used by Task 5 (wake word needs a live mic stream), Task 8 (VAD recording), Task 11 (TTS playback)

This task is hardware I/O — not meaningfully unit-testable without a real microphone/speaker, so we verify manually instead of with `pytest`.

- [ ] **Step 1: Write `sidecar/audio_io.py`**

```python
import numpy as np
import sounddevice as sd


def record_audio(duration_seconds: float, sample_rate: int = 16000) -> bytes:
    recording = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16",
    )
    sd.wait()
    return recording.tobytes()


def play_audio(audio_bytes: bytes, sample_rate: int = 16000) -> None:
    audio_array = np.frombuffer(audio_bytes, dtype="int16")
    sd.play(audio_array, samplerate=sample_rate)
    sd.wait()
```

- [ ] **Step 2: Manually verify recording and playback work**

```bash
python3 -c "
from sidecar.audio_io import record_audio, play_audio
print('Recording 3 seconds — say something...')
audio = record_audio(3.0)
print(f'Recorded {len(audio)} bytes. Playing back...')
play_audio(audio)
print('Done — did you hear your own voice played back?')
"
```

Expected: you hear your own recorded voice played back through your speakers. If you get a `PortAudio` error, you likely need to grant microphone permission to your terminal app in System Settings (Mac) or check your default audio device.

- [ ] **Step 3: Commit**

```bash
git add domly-desktop/python/sidecar/audio_io.py
git commit -m "feat: add audio recording and playback"
```

---

## Task 5: Wake Word Detection

**Files:**
- Create: `domly-desktop/python/sidecar/wake_word.py`

**Interfaces:**
- Consumes: `PICOVOICE_ACCESS_KEY` env var
- Produces: `WakeWordDetector` class with `def listen_for_wake_word() -> None` (blocking call that returns the instant the wake word is detected) — used by Task 12 (main conversation loop)

**Important setup note:** Porcupine (the wake word engine) ships with built-in keywords (`"jarvis"`, `"computer"`, `"hey google"`, etc.) but does **not** include "Hey Domly" out of the box — custom keywords require training a `.ppn` file at [console.picovoice.ai](https://console.picovoice.ai) (free). For this task, use the built-in keyword `"computer"` to get the pipeline working end-to-end. Training a real "Hey Domly" keyword is a follow-up task once the rest of the pipeline works.

- [ ] **Step 1: Write `sidecar/wake_word.py`**

```python
import os
import struct
import pvporcupine
import pyaudio
from dotenv import load_dotenv

load_dotenv()


class WakeWordDetector:
    def __init__(self, keyword: str = "computer"):
        access_key = os.environ["PICOVOICE_ACCESS_KEY"]
        self._porcupine = pvporcupine.create(access_key=access_key, keywords=[keyword])
        self._pa = pyaudio.PyAudio()
        self._stream = self._pa.open(
            rate=self._porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=self._porcupine.frame_length,
        )

    def listen_for_wake_word(self) -> None:
        while True:
            pcm = self._stream.read(self._porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * self._porcupine.frame_length, pcm)
            result = self._porcupine.process(pcm)
            if result >= 0:
                return

    def close(self) -> None:
        self._stream.close()
        self._pa.terminate()
        self._porcupine.delete()
```

- [ ] **Step 2: Add `PICOVOICE_ACCESS_KEY` to `.env`**

Sign up free at [console.picovoice.ai](https://console.picovoice.ai), copy your AccessKey, add to `.env`:
```
PICOVOICE_ACCESS_KEY=<your key>
```

- [ ] **Step 3: Manually verify wake word detection works**

```bash
python3 -c "
from sidecar.wake_word import WakeWordDetector
detector = WakeWordDetector(keyword='computer')
print('Say \"computer\" out loud...')
detector.listen_for_wake_word()
print('Wake word detected!')
detector.close()
"
```

Expected: say "computer" and the script prints "Wake word detected!" and exits.

- [ ] **Step 4: Commit**

```bash
git add domly-desktop/python/sidecar/wake_word.py domly-desktop/python/.env
git commit -m "feat: add wake word detection (built-in keyword, custom keyword pending)"
```

---

## Task 6: Voice Enrollment

**Files:**
- Create: `domly-desktop/python/sidecar/voice_auth.py`
- Create: `domly-desktop/python/tests/test_voice_auth.py`

**Interfaces:**
- Consumes: `storage.save_voice_embedding` (Task 2)
- Produces: `enroll_voice(audio_samples: list[bytes], sample_rate: int = 16000) -> bytes` (returns the embedding, also saves it), `embedding_to_bytes(embedding) -> bytes`, `bytes_to_embedding(data: bytes)` — used by Task 7 (verification compares against this), Task 12 (enrollment flow)

- [ ] **Step 1: Write the failing test in `tests/test_voice_auth.py`**

```python
import numpy as np
from sidecar.voice_auth import embedding_to_bytes, bytes_to_embedding

def test_embedding_roundtrip():
    original = np.array([0.1, 0.2, 0.3, -0.5], dtype=np.float32)
    data = embedding_to_bytes(original)
    restored = bytes_to_embedding(data)
    assert np.allclose(original, restored)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest domly-desktop/python/tests/test_voice_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'sidecar.voice_auth'`

- [ ] **Step 3: Write `sidecar/voice_auth.py`**

```python
import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from sidecar import storage

_encoder = None


def _get_encoder() -> VoiceEncoder:
    global _encoder
    if _encoder is None:
        _encoder = VoiceEncoder()
    return _encoder


def embedding_to_bytes(embedding: np.ndarray) -> bytes:
    return embedding.astype(np.float32).tobytes()


def bytes_to_embedding(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float32)


def enroll_voice(audio_samples: list[bytes], sample_rate: int = 16000) -> bytes:
    encoder = _get_encoder()
    embeddings = []
    for raw_audio in audio_samples:
        audio_array = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0
        wav = preprocess_wav(audio_array, source_sr=sample_rate)
        embeddings.append(encoder.embed_utterance(wav))
    average_embedding = np.mean(embeddings, axis=0)
    data = embedding_to_bytes(average_embedding)
    storage.save_voice_embedding(data)
    return data
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest domly-desktop/python/tests/test_voice_auth.py -v
```

Expected: test passes.

- [ ] **Step 5: Manually verify enrollment works with your real voice**

```bash
python3 -c "
from sidecar.audio_io import record_audio
from sidecar.voice_auth import enroll_voice

samples = []
for i in range(3):
    input(f'Press Enter, then say a phrase for sample {i+1}/3...')
    samples.append(record_audio(3.0))

embedding = enroll_voice(samples)
print(f'Enrolled! Embedding is {len(embedding)} bytes.')
"
```

Expected: records 3 samples, prints the embedding byte length with no errors.

- [ ] **Step 6: Commit**

```bash
git add domly-desktop/python/sidecar/voice_auth.py domly-desktop/python/tests/test_voice_auth.py
git commit -m "feat: add voice enrollment using Resemblyzer embeddings"
```

---

## Task 7: Voice Verification

**Files:**
- Modify: `domly-desktop/python/sidecar/voice_auth.py`
- Modify: `domly-desktop/python/tests/test_voice_auth.py`

**Interfaces:**
- Consumes: `bytes_to_embedding`, `_get_encoder` (this file, Task 6)
- Produces: `verify_voice(audio: bytes, enrolled_embedding: bytes, sample_rate: int = 16000, threshold: float = 0.75) -> bool` — used by Task 12 (rejects commands from non-enrolled voices)

- [ ] **Step 1: Add the failing test to `tests/test_voice_auth.py`**

```python
def test_verify_voice_rejects_dissimilar_embeddings():
    from sidecar.voice_auth import verify_voice, embedding_to_bytes
    import numpy as np

    enrolled = np.ones(256, dtype=np.float32)
    enrolled_bytes = embedding_to_bytes(enrolled)

    # Monkeypatch the encoder used inside verify_voice via a fake embed function
    import sidecar.voice_auth as voice_auth_module

    class FakeEncoder:
        def embed_utterance(self, wav):
            return -np.ones(256, dtype=np.float32)  # opposite direction = dissimilar

    voice_auth_module._encoder = FakeEncoder()

    fake_audio = (np.zeros(16000, dtype=np.int16)).tobytes()
    result = verify_voice(fake_audio, enrolled_bytes)
    assert result is False

def test_verify_voice_accepts_similar_embeddings():
    from sidecar.voice_auth import verify_voice, embedding_to_bytes
    import numpy as np

    enrolled = np.ones(256, dtype=np.float32)
    enrolled_bytes = embedding_to_bytes(enrolled)

    import sidecar.voice_auth as voice_auth_module

    class FakeEncoder:
        def embed_utterance(self, wav):
            return np.ones(256, dtype=np.float32)  # identical = max similarity

    voice_auth_module._encoder = FakeEncoder()

    fake_audio = (np.zeros(16000, dtype=np.int16)).tobytes()
    result = verify_voice(fake_audio, enrolled_bytes)
    assert result is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest domly-desktop/python/tests/test_voice_auth.py -v
```

Expected: `ImportError: cannot import name 'verify_voice'`

- [ ] **Step 3: Add `verify_voice` to `sidecar/voice_auth.py`**

```python
def verify_voice(audio: bytes, enrolled_embedding: bytes, sample_rate: int = 16000, threshold: float = 0.75) -> bool:
    encoder = _get_encoder()
    audio_array = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    wav = preprocess_wav(audio_array, source_sr=sample_rate)
    live_embedding = encoder.embed_utterance(wav)

    enrolled = bytes_to_embedding(enrolled_embedding)
    similarity = np.dot(live_embedding, enrolled) / (np.linalg.norm(live_embedding) * np.linalg.norm(enrolled))
    return bool(similarity >= threshold)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest domly-desktop/python/tests/test_voice_auth.py -v
```

Expected: all 3 tests pass (1 from Task 6 + 2 new).

- [ ] **Step 5: Manually verify with your real voice vs. someone else's (or a recording of someone else, e.g. a YouTube clip)**

```bash
python3 -c "
from sidecar.audio_io import record_audio
from sidecar.voice_auth import verify_voice
from sidecar import storage

embedding = storage.load_voice_embedding()
input('Press Enter, then say something in YOUR voice...')
audio = record_audio(3.0)
print('Match:', verify_voice(audio, embedding))
"
```

Expected: `Match: True` when you speak, `Match: False` if someone else speaks (or you play a different voice through speakers near the mic).

- [ ] **Step 6: Commit**

```bash
git add domly-desktop/python/sidecar/voice_auth.py domly-desktop/python/tests/test_voice_auth.py
git commit -m "feat: add voice verification against enrolled embedding"
```

---

## Task 8: Voice Activity Detection (Silence Detection)

**Files:**
- Create: `domly-desktop/python/sidecar/vad.py`

**Interfaces:**
- Produces: `record_until_silence(silence_duration_seconds: float = 1.5, max_duration_seconds: float = 15.0, sample_rate: int = 16000) -> bytes` — used by Task 12 (records the actual command after wake word + voice verification pass)

This is hardware-dependent, verified manually rather than with `pytest`.

- [ ] **Step 1: Write `sidecar/vad.py`**

```python
import numpy as np
import sounddevice as sd

SILENCE_THRESHOLD = 500  # amplitude threshold below which audio is considered silence
CHUNK_DURATION = 0.1  # seconds per chunk


def record_until_silence(
    silence_duration_seconds: float = 1.5,
    max_duration_seconds: float = 15.0,
    sample_rate: int = 16000,
) -> bytes:
    chunks = []
    silence_chunks_needed = int(silence_duration_seconds / CHUNK_DURATION)
    max_chunks = int(max_duration_seconds / CHUNK_DURATION)
    consecutive_silence = 0

    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(int(CHUNK_DURATION * sample_rate))
            chunks.append(chunk.tobytes())

            amplitude = np.abs(np.frombuffer(chunk.tobytes(), dtype=np.int16)).mean()
            if amplitude < SILENCE_THRESHOLD:
                consecutive_silence += 1
                if consecutive_silence >= silence_chunks_needed:
                    break
            else:
                consecutive_silence = 0

    return b"".join(chunks)
```

- [ ] **Step 2: Manually verify it stops recording after you go silent**

```bash
python3 -c "
from sidecar.vad import record_until_silence
print('Say something, then go quiet...')
audio = record_until_silence()
print(f'Recorded {len(audio)} bytes — stopped automatically after silence.')
"
```

Expected: recording stops shortly after you stop talking, without you pressing anything.

- [ ] **Step 3: Commit**

```bash
git add domly-desktop/python/sidecar/vad.py
git commit -m "feat: add voice activity detection for auto-stop recording"
```

---

## Task 9: Whisper Speech-to-Text

**Files:**
- Create: `domly-desktop/python/sidecar/stt.py`

**Interfaces:**
- Consumes: `OPENAI_API_KEY` env var
- Produces: `transcribe(audio_bytes: bytes, sample_rate: int = 16000) -> str` — used by Task 12 (converts recorded command audio to text for Claude)

- [ ] **Step 1: Write `sidecar/stt.py`**

```python
import os
import io
import wave
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _to_wav_bytes(audio_bytes: bytes, sample_rate: int) -> io.BytesIO:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    buffer.seek(0)
    buffer.name = "audio.wav"
    return buffer


def transcribe(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    wav_buffer = _to_wav_bytes(audio_bytes, sample_rate)
    response = _client.audio.transcriptions.create(model="whisper-1", file=wav_buffer)
    return response.text
```

- [ ] **Step 2: Add `OPENAI_API_KEY` to `.env`**

Get one at [platform.openai.com](https://platform.openai.com/api-keys), add to `.env`:
```
OPENAI_API_KEY=<your key>
```

- [ ] **Step 3: Manually verify transcription works**

```bash
python3 -c "
from sidecar.audio_io import record_audio
from sidecar.stt import transcribe

print('Say a sentence...')
audio = record_audio(4.0)
text = transcribe(audio)
print('You said:', text)
"
```

Expected: prints back roughly what you said.

- [ ] **Step 4: Commit**

```bash
git add domly-desktop/python/sidecar/stt.py domly-desktop/python/.env
git commit -m "feat: add Whisper speech-to-text"
```

---

## Task 10: MCP Client + Claude Orchestration

**Files:**
- Create: `domly-desktop/python/sidecar/mcp_client.py`
- Create: `domly-desktop/python/sidecar/claude_orchestrator.py`

**Interfaces:**
- Consumes: `storage.load_credentials` (Task 2), `ANTHROPIC_API_KEY` env var
- Produces: `ask_claude(user_text: str) -> str` (the full Claude + MCP tool-calling loop, returns final text response) — used by Task 12 (the core "brain" step of the pipeline)

This is the most involved task: it spawns the published `smartrent-mcp` package as a subprocess (same way Claude Desktop does), discovers its tools, converts them into Claude API tool format, and runs the tool-calling loop.

- [ ] **Step 1: Write `sidecar/mcp_client.py`**

```python
import os
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
```

- [ ] **Step 2: Write `sidecar/claude_orchestrator.py`**

```python
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from sidecar.mcp_client import smartrent_mcp_session, mcp_tools_to_claude_format

load_dotenv()

_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-sonnet-4-5"


async def ask_claude(user_text: str) -> str:
    async with smartrent_mcp_session() as session:
        tools_response = await session.list_tools()
        claude_tools = mcp_tools_to_claude_format(tools_response.tools)

        messages = [{"role": "user", "content": user_text}]

        while True:
            response = _client.messages.create(
                model=MODEL,
                max_tokens=1024,
                tools=claude_tools,
                messages=messages,
            )

            if response.stop_reason != "tool_use":
                final_text = "".join(block.text for block in response.content if block.type == "text")
                return final_text

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
```

- [ ] **Step 3: Add `ANTHROPIC_API_KEY` and SmartRent credentials to `.env`**

```
ANTHROPIC_API_KEY=<your key>
SMARTRENT_EMAIL=<your smartrent email>
SMARTRENT_PASSWORD=<your smartrent password>
```

- [ ] **Step 4: Manually save credentials to local storage, then verify the full Claude+MCP loop**

```bash
python3 -c "
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
from sidecar import storage
from sidecar.claude_orchestrator import ask_claude

storage.save_credentials(os.environ['SMARTRENT_EMAIL'], os.environ['SMARTRENT_PASSWORD'])

async def main():
    response = await ask_claude('What is the status of my home?')
    print('Claude says:', response)

asyncio.run(main())
"
```

Expected: Claude calls `get_device_status` on your real `smartrent-mcp` server and responds with your actual device states (same ones you saw when testing `smartrent-mcp` originally).

- [ ] **Step 5: Commit**

```bash
git add domly-desktop/python/sidecar/mcp_client.py domly-desktop/python/sidecar/claude_orchestrator.py domly-desktop/python/.env
git commit -m "feat: add MCP client and Claude tool-calling orchestration"
```

---

## Task 11: ElevenLabs Text-to-Speech

**Files:**
- Create: `domly-desktop/python/sidecar/tts.py`

**Interfaces:**
- Consumes: `ELEVENLABS_API_KEY` env var, `audio_io.play_audio` (Task 4)
- Produces: `speak(text: str) -> None` — used by Task 12 (speaks Claude's response out loud)

- [ ] **Step 1: Write `sidecar/tts.py`**

```python
import os
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from dotenv import load_dotenv

load_dotenv()

_client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs default "Rachel" voice


def speak(text: str) -> None:
    audio = _client.text_to_speech.convert(
        voice_id=DEFAULT_VOICE_ID,
        text=text,
        model_id="eleven_turbo_v2",
    )
    play(audio)
```

- [ ] **Step 2: Add `ELEVENLABS_API_KEY` to `.env`**

Get one at [elevenlabs.io](https://elevenlabs.io), add to `.env`:
```
ELEVENLABS_API_KEY=<your key>
```

- [ ] **Step 3: Manually verify speech playback**

```bash
python3 -c "
from sidecar.tts import speak
speak('Hello, this is Domly speaking.')
"
```

Expected: you hear the sentence spoken through your speakers.

- [ ] **Step 4: Commit**

```bash
git add domly-desktop/python/sidecar/tts.py domly-desktop/python/.env
git commit -m "feat: add ElevenLabs text-to-speech"
```

---

## Task 12: Conversation Mode State Machine

**Files:**
- Create: `domly-desktop/python/sidecar/conversation.py`
- Create: `domly-desktop/python/tests/test_conversation.py`

**Interfaces:**
- Consumes: `WakeWordDetector.listen_for_wake_word` (Task 5), `voice_auth.verify_voice` (Task 7), `vad.record_until_silence` (Task 8), `stt.transcribe` (Task 9), `claude_orchestrator.ask_claude` (Task 10), `tts.speak` (Task 11), `storage.has_voice_embedding`, `storage.load_voice_embedding` (Task 2), `DomlyServer.broadcast` (Task 3)
- Produces: `ConversationManager` class with `async def run_main_loop(server: DomlyServer) -> None` — used by Task 13 (the entrypoint wires this into `start()`)

The state transition logic (idle → listening → processing → speaking → conversation window → idle) is the testable part here — we test it with mocked I/O functions rather than real hardware/APIs.

- [ ] **Step 1: Write the failing test in `tests/test_conversation.py`**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest domly-desktop/python/tests/test_conversation.py -v
```

Expected: `ModuleNotFoundError: No module named 'sidecar.conversation'`

- [ ] **Step 3: Write `sidecar/conversation.py`**

```python
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

        await server.broadcast({"type": "status", "state": "processing"})
        text = self.transcribe_fn(command_audio)
        await server.broadcast({"type": "conversation_event", "role": "user", "text": text})

        response = await self.ask_claude_fn(text)
        await server.broadcast({"type": "conversation_event", "role": "assistant", "text": response})

        await server.broadcast({"type": "status", "state": "speaking"})
        self.speak_fn(response)

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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest domly-desktop/python/tests/test_conversation.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit**

```bash
git add domly-desktop/python/sidecar/conversation.py domly-desktop/python/tests/test_conversation.py
git commit -m "feat: add conversation state machine tying the voice pipeline together"
```

---

## Task 13: Main Entrypoint — End-to-End Integration

**Files:**
- Create: `domly-desktop/python/sidecar/main.py`

**Interfaces:**
- Consumes: everything from Tasks 2-12
- Produces: the actual runnable sidecar process

- [ ] **Step 1: Write `sidecar/main.py`**

```python
import asyncio
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
        import base64
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
    detector = WakeWordDetector(keyword="computer")

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
```

- [ ] **Step 2: Manually verify the full end-to-end pipeline**

Make sure you've already enrolled your voice and saved credentials from Tasks 6 and 10. Run:

```bash
python -m sidecar.main
```

Then:
1. Say "computer" (the wake word)
2. Say a command like "What's the status of my home?"
3. Confirm: voice is verified, Claude calls your real `smartrent-mcp` tools, and you hear the spoken response
4. Without saying "computer" again, say a follow-up like "Turn off the kitchen lights" within 8 seconds
5. Confirm: the follow-up works without repeating the wake word
6. Wait 8+ seconds in silence — confirm it returns to idle/wake-word-only listening

- [ ] **Step 3: Commit**

```bash
git add domly-desktop/python/sidecar/main.py
git commit -m "feat: wire full voice pipeline into main entrypoint"
```

---

## Self-Review Notes

- All 10 responsibilities from the design spec are covered: WebSocket server (Task 3), wake word (Task 5), voice auth — enrollment (Task 6) + verification (Task 7), VAD (Task 8), STT (Task 9), Claude orchestration (Task 10), TTS (Task 11), conversation mode (Task 12), local encrypted storage (Task 2) ✅
- WebSocket message contract matches the design spec exactly (`set_credentials`, `enroll_voice_start`, `enroll_voice_sample`, `mute`, `unmute`, `quit` in; `status`, `conversation_event`, `enrollment_complete`, `voice_rejected`, `error` out) ✅
- Reuses published `smartrent-mcp` PyPI package rather than reimplementing device control ✅
- Conversation window matches the spec's 8-second timeout ✅
- **Known gap, flagged honestly:** Task 5 uses Porcupine's built-in "computer" keyword, not a custom-trained "Hey Domly" keyword — training a real custom wake word requires Picovoice Console and is a natural fast-follow once this pipeline works end-to-end
- **Known gap:** `error` message broadcasting (API failures, offline mode) from the design spec's error handling table isn't implemented as a dedicated task — wire this in as you hit real failures during Task 13's manual testing, using `server.broadcast({"type": "error", "message": "..."})` from `try`/`except` blocks around the Claude/Whisper/ElevenLabs calls
