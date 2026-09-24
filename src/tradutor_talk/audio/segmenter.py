from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from math import ceil


class SpeechStartTimeout(TimeoutError):
    pass


class SegmentState(StrEnum):
    WAITING = "waiting"
    CAPTURING = "capturing"
    COMPLETE = "complete"


@dataclass(slots=True, frozen=True)
class SegmenterConfig:
    block_ms: int = 20
    pre_roll_ms: int = 200
    start_speech_ms: int = 60
    end_silence_ms: int = 600
    wait_timeout_seconds: float = 30.0
    max_utterance_seconds: float = 20.0

    def __post_init__(self) -> None:
        if self.block_ms not in {10, 20, 30}:
            raise ValueError("block_ms must be 10, 20 or 30")
        if self.pre_roll_ms < 0:
            raise ValueError("pre_roll_ms must be >= 0")
        if self.start_speech_ms <= 0:
            raise ValueError("start_speech_ms must be > 0")
        if self.end_silence_ms <= 0:
            raise ValueError("end_silence_ms must be > 0")
        if self.wait_timeout_seconds <= 0:
            raise ValueError("wait_timeout_seconds must be > 0")
        if self.max_utterance_seconds <= 0:
            raise ValueError("max_utterance_seconds must be > 0")


class SpeechSegmenter:
    """Pure frame state machine used before STT.

    The class knows nothing about microphones or a specific VAD implementation.
    That makes speech-boundary behavior deterministic and unit-testable.
    """

    def __init__(self, config: SegmenterConfig | None = None) -> None:
        self.config = config or SegmenterConfig()

        self._pre_roll_frames = max(
            1,
            ceil(self.config.pre_roll_ms / self.config.block_ms),
        )
        self._start_frames = max(
            1,
            ceil(self.config.start_speech_ms / self.config.block_ms),
        )
        self._end_frames = max(
            1,
            ceil(self.config.end_silence_ms / self.config.block_ms),
        )
        self._wait_frames = max(
            1,
            ceil(
                self.config.wait_timeout_seconds
                * 1000
                / self.config.block_ms
            ),
        )
        self._max_capture_frames = max(
            1,
            ceil(
                self.config.max_utterance_seconds
                * 1000
                / self.config.block_ms
            ),
        )

        self._pre_roll: deque[bytes] = deque(maxlen=self._pre_roll_frames)
        self._captured: list[bytes] = []
        self._speech_run = 0
        self._silence_run = 0
        self._frames_seen = 0
        self._triggered = False
        self._complete = False
        self._ended_by_max_duration = False

    @property
    def state(self) -> SegmentState:
        if self._complete:
            return SegmentState.COMPLETE
        if self._triggered:
            return SegmentState.CAPTURING
        return SegmentState.WAITING

    @property
    def ended_by_max_duration(self) -> bool:
        return self._ended_by_max_duration

    @property
    def pcm(self) -> bytes:
        if not self._complete:
            raise RuntimeError("segment is not complete")
        return b"".join(self._captured)

    def feed(self, frame: bytes, *, is_speech: bool) -> SegmentState:
        if self._complete:
            raise RuntimeError("segment is already complete")
        if not frame:
            raise ValueError("frame cannot be empty")

        self._frames_seen += 1

        if not self._triggered:
            self._pre_roll.append(bytes(frame))
            self._speech_run = self._speech_run + 1 if is_speech else 0

            if self._speech_run >= self._start_frames:
                self._triggered = True
                self._captured.extend(self._pre_roll)
                self._pre_roll.clear()
                return SegmentState.CAPTURING

            if self._frames_seen >= self._wait_frames:
                raise SpeechStartTimeout(
                    f"no speech detected within {self.config.wait_timeout_seconds}s"
                )

            return SegmentState.WAITING

        self._captured.append(bytes(frame))
        self._silence_run = 0 if is_speech else self._silence_run + 1

        if len(self._captured) >= self._max_capture_frames:
            self._ended_by_max_duration = True
            self._complete = True
            return SegmentState.COMPLETE

        if self._silence_run >= self._end_frames:
            self._complete = True
            return SegmentState.COMPLETE

        return SegmentState.CAPTURING
