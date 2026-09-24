from __future__ import annotations

from collections.abc import Mapping, Sequence

from tradutor_talk.core.models import ConversationTurn, SpeechSynthesisResult, Transcript, TranslationResult


class MockSTTProvider:
    async def transcribe(self, audio: bytes, *, language_hint: str | None = None) -> Transcript:
        return Transcript(text=audio.decode("utf-8"), detected_language=language_hint or "und", confidence=1.0)


class MockTranslationProvider:
    _translations = {
        ("en-US", "pt-BR", "Good morning"): "Bom dia",
        ("pt-BR", "en-US", "Bom dia"): "Good morning",
        ("en-US", "pt-BR", "How are you?"): "Como você está?",
        ("pt-BR", "en-US", "Como você está?"): "How are you?",
    }

    async def translate(self, *, text: str, source_language: str, target_language: str,
                        context: Sequence[ConversationTurn], glossary: Mapping[str, str]) -> TranslationResult:
        translated = self._translations.get((source_language, target_language, text), f"[{target_language}] {text}")
        for term, replacement in glossary.items():
            translated = translated.replace(term, replacement)
        return TranslationResult(text=translated, source_language=source_language, target_language=target_language)


class MockTTSProvider:
    async def synthesize(self, *, text: str, language: str) -> SpeechSynthesisResult:
        return SpeechSynthesisResult(audio=text.encode("utf-8"), media_type="audio/mock", voice=f"mock-{language}")
