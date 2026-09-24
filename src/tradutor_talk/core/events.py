from dataclasses import dataclass, field
from enum import StrEnum
from time import time
from typing import Any


class EventType(StrEnum):
    STATE_CHANGED = "state_changed"
    UTTERANCE_STARTED = "utterance_started"
    UTTERANCE_COMPLETED = "utterance_completed"
    UTTERANCE_CANCELLED = "utterance_cancelled"
    PROVIDER_ERROR = "provider_error"


@dataclass(slots=True, frozen=True)
class SessionEvent:
    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time)
