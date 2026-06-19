import numpy as np
from sidecar.voice_auth import embedding_to_bytes, bytes_to_embedding

def test_embedding_roundtrip():
    original = np.array([0.1, 0.2, 0.3, -0.5], dtype=np.float32)
    data = embedding_to_bytes(original)
    restored = bytes_to_embedding(data)
    assert np.allclose(original, restored)

def test_verify_voice_rejects_dissimilar_embeddings():
    from sidecar.voice_auth import verify_voice, embedding_to_bytes
    import numpy as np

    enrolled = np.ones(256, dtype=np.float32)
    enrolled_bytes = embedding_to_bytes(enrolled)

    import sidecar.voice_auth as voice_auth_module

    class FakeEncoder:
        def embed_utterance(self, wav):
            return -np.ones(256, dtype=np.float32)

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
            return np.ones(256, dtype=np.float32)

    voice_auth_module._encoder = FakeEncoder()

    fake_audio = (np.zeros(16000, dtype=np.int16)).tobytes()
    result = verify_voice(fake_audio, enrolled_bytes)
    assert result is True
