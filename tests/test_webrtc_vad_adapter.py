import sys
from types import SimpleNamespace

import pytest

from tradutor_talk.audio.vad import VoiceActivity
from tradutor_talk.audio.webrtc_vad import WebRTCVAD


class FakeVad:
    def __init__(self, mode: int) -> None:
        self.mode = mode

    def is_speech(self, frame: bytes, sample_rate: int) -> bool:
        return any(frame)


def test_webrtc_adapter_accepts_20ms_pcm16_without_real_dependency(
    monkeypatch,
) -> None:
    monkeypatch.setitem(
        sys.modules,
        "webrtcvad",
        SimpleNamespace(Vad=FakeVad),
    )

    vad = WebRTCVAD(aggressiveness=2)
    speech_frame = b"\x01\x00" * 320
    silence_frame = b"\x00\x00" * 320

    assert (
        vad.process(speech_frame, sample_rate=16000).activity
        is VoiceActivity.SPEECH
    )
    assert (
        vad.process(silence_frame, sample_rate=16000).activity
        is VoiceActivity.SILENCE
    )


def test_webrtc_adapter_rejects_wrong_frame_duration(monkeypatch) -> None:
    monkeypatch.setitem(
        sys.modules,
        "webrtcvad",
        SimpleNamespace(Vad=FakeVad),
    )

    vad = WebRTCVAD()

    with pytest.raises(ValueError):
        vad.process(b"\x00\x00" * 100, sample_rate=16000)
