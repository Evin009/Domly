def test_speak_converts_text_and_plays_audio(monkeypatch):
    import sidecar.tts as tts_module

    class FakeTextToSpeech:
        def convert(self, voice_id, text, model_id):
            assert text == "hello"
            return b"fake_audio_bytes"

    class FakeClient:
        text_to_speech = FakeTextToSpeech()

    tts_module._client = FakeClient()

    played = []
    monkeypatch.setattr(tts_module, "_play_audio", lambda audio: played.append(audio))

    tts_module.speak("hello")

    assert played == [b"fake_audio_bytes"]
