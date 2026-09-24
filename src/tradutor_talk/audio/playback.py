from __future__ import annotations

import asyncio
from dataclasses import dataclass
from io import BytesIO
import wave


class AudioPlaybackError(RuntimeError):
    pass


@dataclass(slots=True, frozen=True)
class WavInfo:
    sample_rate: int
    channels: int
    sample_width: int
    frames: int


def inspect_wav(audio: bytes) -> WavInfo:
    if not audio:
        raise ValueError("audio cannot be empty")

    try:
        with wave.open(BytesIO(audio), "rb") as wav:
            return WavInfo(
                sample_rate=wav.getframerate(),
                channels=wav.getnchannels(),
                sample_width=wav.getsampwidth(),
                frames=wav.getnframes(),
            )
    except (wave.Error, EOFError) as exc:
        raise AudioPlaybackError(f"invalid WAV audio: {exc}") from exc


class SoundDevicePlayer:
    def __init__(
        self,
        *,
        device: int | str | None = None,
        chunk_frames: int = 2_048,
    ) -> None:
        if chunk_frames < 1:
            raise ValueError("chunk_frames must be >= 1")
        self.device = device
        self.chunk_frames = chunk_frames

    async def play_wav(self, audio: bytes) -> None:
        await asyncio.to_thread(self._play_wav_blocking, audio)

    def _play_wav_blocking(self, audio: bytes) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise AudioPlaybackError("sounddevice is not installed") from exc

        try:
            with wave.open(BytesIO(audio), "rb") as wav:
                if wav.getsampwidth() != 2:
                    raise AudioPlaybackError(
                        f"unsupported WAV sample width: {wav.getsampwidth()}"
                    )
                if wav.getcomptype() != "NONE":
                    raise AudioPlaybackError(
                        f"compressed WAV is not supported: {wav.getcomptype()}"
                    )

                with sd.RawOutputStream(
                    samplerate=wav.getframerate(),
                    channels=wav.getnchannels(),
                    dtype="int16",
                    device=self.device,
                ) as stream:
                    while True:
                        chunk = wav.readframes(self.chunk_frames)
                        if not chunk:
                            break
                        underflowed = stream.write(chunk)
                        if underflowed:
                            raise AudioPlaybackError("speaker output underflow")
        except AudioPlaybackError:
            raise
        except (wave.Error, EOFError) as exc:
            raise AudioPlaybackError(f"invalid WAV audio: {exc}") from exc
        except Exception as exc:
            raise AudioPlaybackError(f"audio playback failed: {exc}") from exc
