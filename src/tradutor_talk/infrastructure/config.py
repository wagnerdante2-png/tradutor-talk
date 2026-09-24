from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True, frozen=True)
class SessionConfig:
    provider_timeout_seconds: float = 10.0


@dataclass(slots=True, frozen=True)
class ContextConfig:
    max_turns: int = 8


@dataclass(slots=True, frozen=True)
class GlossaryConfig:
    path: str = "config/glossary.example.json"


@dataclass(slots=True, frozen=True)
class AudioConfig:
    sample_rate: int = 16000
    channels: int = 1
    block_ms: int = 20
    dtype: str = "int16"

    def __post_init__(self) -> None:
        if self.sample_rate < 8000:
            raise ValueError("sample_rate must be >= 8000")
        if self.channels != 1:
            raise ValueError("M1 supports mono capture only")
        if self.block_ms <= 0:
            raise ValueError("block_ms must be > 0")


@dataclass(slots=True, frozen=True)
class OpenAIProviderConfig:
    stt_model: str = "gpt-transcribe"
    translation_model: str = "gpt-6-luna"
    translation_reasoning_effort: str = "none"
    tts_model: str = "gpt-4o-mini-tts"
    tts_voice: str = "marin"


@dataclass(slots=True, frozen=True)
class AppConfig:
    session: SessionConfig = SessionConfig()
    context: ContextConfig = ContextConfig()
    glossary: GlossaryConfig = GlossaryConfig()
    audio: AudioConfig = AudioConfig()
    openai: OpenAIProviderConfig = OpenAIProviderConfig()


def load_config(path: str | Path) -> AppConfig:
    file_path = Path(path)
    if not file_path.exists():
        return AppConfig()

    raw = tomllib.loads(file_path.read_text(encoding="utf-8"))
    providers = raw.get("providers", {})
    return AppConfig(
        session=SessionConfig(**raw.get("session", {})),
        context=ContextConfig(**raw.get("context", {})),
        glossary=GlossaryConfig(**raw.get("glossary", {})),
        audio=AudioConfig(**raw.get("audio", {})),
        openai=OpenAIProviderConfig(**providers.get("openai", {})),
    )
