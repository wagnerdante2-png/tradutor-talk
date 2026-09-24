from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from time import perf_counter
from uuid import uuid4


class Direction(StrEnum):
    LOCAL_TO_REMOTE = "local_to_remote"
    REMOTE_TO_LOCAL = "remote_to_local"


class SessionState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    SPEECH_DETECTED = "speech_detected"
    CAPTURING = "capturing"
    END_OF_TURN = "end_of_turn"
    TRANSCRIBING = "transcribing"
    TRANSLATING = "translating"
    SYNTHESIZING = "synthesizing"
    PLAYING = "playing"
    COOLDOWN = "cooldown"
    RECOVERING_NETWORK = "recovering_network"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    AUDIO_DEVICE_LOST = "audio_device_lost"
    RATE_LIMITED = "rate_limited"
    SESSION_ERROR = "session_error"


class UtteranceStatus(StrEnum):
    CREATED = "created"
    TRANSCRIBED = "transcribed"
    TRANSLATED = "translated"
    SYNTHESIZED = "synthesized"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(slots=True, frozen=True)
class Transcript:
    text: str
    detected_language: str
    confidence: float | None = None


@dataclass(slots=True, frozen=True)
class TranslationResult:
    text: str
    source_language: str
    target_language: str


@dataclass(slots=True, frozen=True)
class SpeechSynthesisResult:
    audio: bytes
    media_type: str = "audio/raw"
    voice: str = "default"


@dataclass(slots=True, frozen=True)
class ConversationTurn:
    direction: Direction
    source_language: str
    target_language: str
    original_text: str
    translated_text: str


@dataclass(slots=True)
class Utterance:
    direction: Direction
    source_language: str
    target_language: str
    id: str = field(default_factory=lambda: f"UTT-{uuid4().hex[:12].upper()}")
    status: UtteranceStatus = UtteranceStatus.CREATED
    original_text: str = ""
    translated_text: str = ""
    detected_language: str | None = None
    started_at: float = field(default_factory=perf_counter)
    finished_at: float | None = None
    stage_latency_ms: dict[str, float] = field(default_factory=dict)

    @property
    def total_latency_ms(self) -> float:
        end = self.finished_at if self.finished_at is not None else perf_counter()
        return (end - self.started_at) * 1000


@dataclass(slots=True, frozen=True)
class ProcessResult:
    utterance: Utterance
    speech: SpeechSynthesisResult
