import numpy as np
from sidecar.voice_auth import embedding_to_bytes, bytes_to_embedding

def test_embedding_roundtrip():
    original = np.array([0.1, 0.2, 0.3, -0.5], dtype=np.float32)
    data = embedding_to_bytes(original)
    restored = bytes_to_embedding(data)
    assert np.allclose(original, restored)
