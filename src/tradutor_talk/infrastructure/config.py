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
class AppConfig:
    session: SessionConfig = SessionConfig()
    context: ContextConfig = ContextConfig()
    glossary: GlossaryConfig = GlossaryConfig()


def load_config(path: str | Path) -> AppConfig:
    file_path = Path(path)
    if not file_path.exists():
        return AppConfig()
    raw = tomllib.loads(file_path.read_text(encoding="utf-8"))
    return AppConfig(
        session=SessionConfig(**raw.get("session", {})),
        context=ContextConfig(**raw.get("context", {})),
        glossary=GlossaryConfig(**raw.get("glossary", {})),
    )
