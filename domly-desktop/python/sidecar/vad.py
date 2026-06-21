import numpy as np
import sounddevice as sd

SILENCE_THRESHOLD = 50  # amplitude threshold below which audio is considered silence
CHUNK_DURATION = 0.1  # seconds per chunk


def _is_silent(chunk_bytes: bytes, threshold: int = SILENCE_THRESHOLD) -> bool:
    amplitude = np.abs(np.frombuffer(chunk_bytes, dtype=np.int16)).mean()
    return bool(amplitude < threshold)


def _collect_until_silence(
    read_chunk_fn,
    silence_duration_seconds: float = 1.5,
    max_duration_seconds: float = 15.0,
) -> bytes:
    chunks = []
    silence_chunks_needed = int(silence_duration_seconds / CHUNK_DURATION)
    max_chunks = int(max_duration_seconds / CHUNK_DURATION)
    consecutive_silence = 0

    for _ in range(max_chunks):
        chunk_bytes = read_chunk_fn()
        chunks.append(chunk_bytes)

        if _is_silent(chunk_bytes):
            consecutive_silence += 1
            if consecutive_silence >= silence_chunks_needed:
                break
        else:
            consecutive_silence = 0

    return b"".join(chunks)


def record_until_silence(
    silence_duration_seconds: float = 1.5,
    max_duration_seconds: float = 15.0,
    sample_rate: int = 16000,
) -> bytes:
    with sd.InputStream(samplerate=sample_rate, channels=1, dtype="int16") as stream:
        def read_chunk_fn() -> bytes:
            chunk, _ = stream.read(int(CHUNK_DURATION * sample_rate))
            return chunk.tobytes()

        return _collect_until_silence(read_chunk_fn, silence_duration_seconds, max_duration_seconds)
