from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from tradutor_talk.core.models import ConversationTurn, SpeechSynthesisResult, Transcript, TranslationResult


class STTProvider(Protocol):
    async def transcribe(self, audio: bytes, *, language_hint: str | None = None) -> Transcript:
        ...


class TranslationProvider(Protocol):
    async def translate(self, *, text: str, source_language: str, target_language: str,
                        context: Sequence[ConversationTurn], glossary: Mapping[str, str]) -> TranslationResult:
        ...


class TTSProvider(Protocol):
    async def synthesize(self, *, text: str, language: str) -> SpeechSynthesisResult:
        ...
