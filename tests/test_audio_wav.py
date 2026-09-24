from io import BytesIO
import wave

import pytest

from tradutor_talk.audio.capture import CaptureSettings
from tradutor_talk.audio.wav import pcm16_to_wav


def test_pcm16_to_wav_builds_valid_mono_header() -> None:
    pcm = b"\x00\x00" * 160
    result = pcm16_to_wav(pcm, sample_rate=16000)
    with wave.open(BytesIO(result), "rb") as wav:
        assert wav.getnchannels() == 1
        assert wav.getsampwidth() == 2
        assert wav.getframerate() == 16000
        assert wav.getnframes() == 160


def test_capture_settings_compute_20ms_block() -> None:
    settings = CaptureSettings(sample_rate=16000, block_ms=20)
    assert settings.block_frames == 320


def test_pcm16_to_wav_rejects_empty_audio() -> None:
    with pytest.raises(ValueError):
        pcm16_to_wav(b"", sample_rate=16000)
