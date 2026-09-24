from __future__ import annotations

from io import BytesIO
import wave


def pcm16_to_wav(pcm: bytes, *, sample_rate: int, channels: int = 1) -> bytes:
    if not pcm:
        raise ValueError("pcm cannot be empty")
    if sample_rate < 8000:
        raise ValueError("sample_rate must be >= 8000")
    if channels < 1:
        raise ValueError("channels must be >= 1")

    output = BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return output.getvalue()
