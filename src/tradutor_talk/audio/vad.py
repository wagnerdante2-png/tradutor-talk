from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class VoiceActivity(StrEnum):
    SILENCE = "silence"
    SPEECH_START = "speech_start"
    SPEECH = "speech"
    SPEECH_END = "speech_end"


@dataclass(slots=True, frozen=True)
class VADResult:
    activity: VoiceActivity
    probability: float | None = None


class VADProvider(Protocol):
    def process(self, pcm_chunk: bytes, *, sample_rate: int) -> VADResult:
        ...
