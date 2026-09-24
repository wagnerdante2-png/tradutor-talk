from tradutor_talk.audio.playback import inspect_wav
from tradutor_talk.audio.wav import pcm16_to_wav


def test_inspect_wav_reads_runtime_format() -> None:
    audio = pcm16_to_wav(
        b"\x00\x00" * 320,
        sample_rate=16000,
        channels=1,
    )

    info = inspect_wav(audio)

    assert info.sample_rate == 16000
    assert info.channels == 1
    assert info.sample_width == 2
    assert info.frames == 320
