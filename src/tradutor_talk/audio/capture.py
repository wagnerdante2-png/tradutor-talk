from __future__ import annotations

import asyncio
from dataclasses import dataclass

from tradutor_talk.audio.wav import pcm16_to_wav


class AudioCaptureError(RuntimeError):
    pass


@dataclass(slots=True, frozen=True)
class CaptureSettings:
    sample_rate: int = 16000
    channels: int = 1
    block_ms: int = 20
    dtype: str = "int16"
    device: int | str | None = None

    @property
    def block_frames(self) -> int:
        return max(1, int(self.sample_rate * self.block_ms / 1000))


class SoundDeviceRecorder:
    def __init__(self, settings: CaptureSettings | None = None) -> None:
        self.settings = settings or CaptureSettings()

    async def record_wav(self, seconds: float) -> bytes:
        if seconds <= 0:
            raise ValueError("seconds must be > 0")
        return await asyncio.to_thread(self._record_wav_blocking, seconds)

    def _record_wav_blocking(self, seconds: float) -> bytes:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise AudioCaptureError("sounddevice is not installed") from exc

        settings = self.settings
        remaining = int(settings.sample_rate * seconds)
        chunks: list[bytes] = []

        try:
            with sd.RawInputStream(
                samplerate=settings.sample_rate,
                blocksize=settings.block_frames,
                device=settings.device,
                channels=settings.channels,
                dtype=settings.dtype,
            ) as stream:
                while remaining > 0:
                    frames = min(settings.block_frames, remaining)
                    data, overflowed = stream.read(frames)
                    if overflowed:
                        raise AudioCaptureError("microphone input overflow")
                    chunks.append(bytes(data))
                    remaining -= frames
        except AudioCaptureError:
            raise
        except Exception as exc:
            raise AudioCaptureError(f"microphone capture failed: {exc}") from exc

        pcm = b"".join(chunks)
        if not pcm:
            raise AudioCaptureError("microphone returned no audio")
        return pcm16_to_wav(pcm, sample_rate=settings.sample_rate, channels=settings.channels)
