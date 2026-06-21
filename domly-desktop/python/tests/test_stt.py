import numpy as np
from sidecar.stt import transcribe


def test_transcribe_returns_text_from_whisper_response():
    import sidecar.stt as stt_module

    class FakeTranscription:
        text = "turn on the lights"

    class FakeTranscriptions:
        def create(self, model, file):
            return FakeTranscription()

    class FakeAudio:
        transcriptions = FakeTranscriptions()

    class FakeClient:
        audio = FakeAudio()

    stt_module._client = FakeClient()

    fake_audio = np.zeros(1600, dtype=np.int16).tobytes()
    result = transcribe(fake_audio)

    assert result == "turn on the lights"
