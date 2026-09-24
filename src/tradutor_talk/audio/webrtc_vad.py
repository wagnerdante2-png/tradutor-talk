from __future__ import annotations

from tradutor_talk.audio.vad import VADResult, VoiceActivity


class WebRTCVAD:
    SUPPORTED_SAMPLE_RATES = {8_000, 16_000, 32_000, 48_000}
    SUPPORTED_FRAME_MS = {10, 20, 30}

    def __init__(self, *, aggressiveness: int = 2) -> None:
        if aggressiveness not in {0, 1, 2, 3}:
            raise ValueError("aggressiveness must be between 0 and 3")
        try:
            import webrtcvad
        except ImportError as exc:
            raise RuntimeError("webrtcvad-wheels is not installed") from exc

        self.aggressiveness = aggressiveness
        self._vad = webrtcvad.Vad(aggressiveness)

    def process(
        self,
        pcm_chunk: bytes,
        *,
        sample_rate: int,
    ) -> VADResult:
        if sample_rate not in self.SUPPORTED_SAMPLE_RATES:
            raise ValueError(f"unsupported VAD sample rate: {sample_rate}")
        if not pcm_chunk:
            raise ValueError("pcm_chunk cannot be empty")
        if len(pcm_chunk) % 2 != 0:
            raise ValueError("PCM16 chunk must contain an even number of bytes")

        frame_samples = len(pcm_chunk) // 2
        frame_ms = round((frame_samples / sample_rate) * 1000)
        if frame_ms not in self.SUPPORTED_FRAME_MS:
            raise ValueError(
                f"WebRTC VAD frame must be 10, 20 or 30 ms; received {frame_ms} ms"
            )

        is_speech = bool(self._vad.is_speech(pcm_chunk, sample_rate))
        return VADResult(
            activity=VoiceActivity.SPEECH if is_speech else VoiceActivity.SILENCE,
            probability=None,
        )
