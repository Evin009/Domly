import numpy as np
from resemblyzer import VoiceEncoder, preprocess_wav
from sidecar import storage

_encoder = None  # lazy-loaded so we only load the ML model once, the first time it's needed

# VoiceEncoder is the ML model that turns audio into an embedding.
# Loading it takes a moment, so we only do it once and reuse it.
def _get_encoder() -> VoiceEncoder:
    global _encoder
    if _encoder is None:
        _encoder = VoiceEncoder()
    return _encoder

# Converts the embedding (array of decimal numbers) into raw bytes,
# so storage.py can save it.
def embedding_to_bytes(embedding: np.ndarray) -> bytes:
    return embedding.astype(np.float32).tobytes()

# Reverses embedding_to_bytes — turns raw bytes back into the array.
def bytes_to_embedding(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float32)

def enroll_voice(audio_samples: list[bytes], sample_rate: int = 16000) -> bytes:
    # Takes several recorded voice samples, generates an embedding for
    # each one, averages them together (more stable than just one sample),
    # then saves the result via storage.py.
    encoder = _get_encoder()
    embeddings = []
    for raw_audio in audio_samples:
        # Convert raw int16 audio bytes into the normalized float format Resemblyzer expects
        audio_array = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32) / 32768.0
        wav = preprocess_wav(audio_array, source_sr=sample_rate)
        embeddings.append(encoder.embed_utterance(wav))

    average_embedding = np.mean(embeddings, axis=0)
    data = embedding_to_bytes(average_embedding)
    storage.save_voice_embedding(data)
    return data
