from __future__ import annotations

import asyncio
from dataclasses import dataclass

from tradutor_talk.audio.capture import AudioCaptureError, CaptureSettings
from tradutor_talk.audio.segmenter import (
    SegmentState,
    SegmenterConfig,
    SpeechSegmenter,
)
from tradutor_talk.audio.vad import VADProvider, VoiceActivity
from tradutor_talk.audio.wav import pcm16_to_wav


@dataclass(slots=True, frozen=True)
class HandsFreeSettings:
    capture: CaptureSettings = CaptureSettings()
    segmenter: SegmenterConfig = SegmenterConfig()


class HandsFreeRecorder:
    def __init__(
        self,
        *,
        vad: VADProvider,
        settings: HandsFreeSettings | None = None,
    ) -> None:
        self.vad = vad
        self.settings = settings or HandsFreeSettings()

        if self.settings.capture.dtype != "int16":
            raise ValueError("hands-free VAD requires PCM16 capture")
        if self.settings.capture.channels != 1:
            raise ValueError("hands-free VAD requires mono capture")
        if (
            self.settings.capture.block_ms
            != self.settings.segmenter.block_ms
        ):
            raise ValueError("capture and segmenter block_ms must match")

    async def wait_for_utterance_wav(self) -> bytes:
        return await asyncio.to_thread(self._wait_blocking)

    def _wait_blocking(self) -> bytes:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise AudioCaptureError("sounddevice is not installed") from exc

        capture = self.settings.capture
        segmenter = SpeechSegmenter(self.settings.segmenter)

        try:
            with sd.RawInputStream(
                samplerate=capture.sample_rate,
                blocksize=capture.block_frames,
                device=capture.device,
                channels=capture.channels,
                dtype=capture.dtype,
            ) as stream:
                while True:
                    data, overflowed = stream.read(capture.block_frames)
                    if overflowed:
                        raise AudioCaptureError("microphone input overflow")

                    frame = bytes(data)
                    vad_result = self.vad.process(
                        frame,
                        sample_rate=capture.sample_rate,
                    )
                    state = segmenter.feed(
                        frame,
                        is_speech=vad_result.activity is VoiceActivity.SPEECH,
                    )

                    if state is SegmentState.COMPLETE:
                        return pcm16_to_wav(
                            segmenter.pcm,
                            sample_rate=capture.sample_rate,
                            channels=capture.channels,
                        )
        except AudioCaptureError:
            raise
        except Exception as exc:
            from tradutor_talk.audio.segmenter import SpeechStartTimeout

            if isinstance(exc, SpeechStartTimeout):
                raise
            raise AudioCaptureError(
                f"hands-free microphone capture failed: {exc}"
            ) from exc
