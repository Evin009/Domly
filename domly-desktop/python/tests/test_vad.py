import numpy as np
from sidecar.vad import _is_silent, _collect_until_silence


def _loud_chunk() -> bytes:
    return np.full(1600, 5000, dtype=np.int16).tobytes()


def _silent_chunk() -> bytes:
    return np.zeros(1600, dtype=np.int16).tobytes()


def test_is_silent_true_for_quiet_chunk():
    assert _is_silent(_silent_chunk()) is True


def test_is_silent_false_for_loud_chunk():
    assert _is_silent(_loud_chunk()) is False


def test_stops_after_sustained_silence():
    chunks = [_loud_chunk(), _loud_chunk()] + [_silent_chunk()] * 20
    chunk_iter = iter(chunks)

    result = _collect_until_silence(
        read_chunk_fn=lambda: next(chunk_iter),
        silence_duration_seconds=0.5,  # 5 silent chunks at 0.1s each
        max_duration_seconds=10.0,
    )

    # 2 loud chunks + 5 silent chunks needed to trigger stop = 7 chunks
    assert result == b"".join(chunks[:7])


def test_stops_at_max_duration_if_never_silent():
    chunk_iter = iter([_loud_chunk()] * 100)

    result = _collect_until_silence(
        read_chunk_fn=lambda: next(chunk_iter),
        silence_duration_seconds=1.5,
        max_duration_seconds=0.5,  # caps at 5 chunks
    )

    assert result == b"".join([_loud_chunk()] * 5)
