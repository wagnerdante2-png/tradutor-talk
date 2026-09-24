from __future__ import annotations

import asyncio

from tradutor_talk.core.models import SpeechSynthesisResult


class OpenAITTSProvider:
    def __init__(
        self,
        *,
        model: str = "gpt-4o-mini-tts",
        voice: str = "marin",
        client=None,
    ) -> None:
        self.model = model
        self.voice = voice
        self._client = client

    def _client_or_create(self):
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("openai package is not installed") from exc
        self._client = OpenAI()
        return self._client

    async def synthesize(
        self,
        *,
        text: str,
        language: str,
    ) -> SpeechSynthesisResult:
        source_text = text.strip()
        if not source_text:
            raise ValueError("text cannot be empty")
        if len(source_text) > 4_096:
            raise ValueError("text exceeds TTS live-utterance limit")

        instructions = (
            f"Speak naturally and clearly in locale {language}. "
            "Preserve the meaning, names, numbers, and conversational tone. "
            "Do not add words that are not present in the input."
        )

        client = self._client_or_create()
        response = await asyncio.to_thread(
            client.audio.speech.create,
            model=self.model,
            voice=self.voice,
            input=source_text,
            instructions=instructions,
            response_format="wav",
        )

        audio = bytes(response.content)
        if not audio:
            raise RuntimeError("TTS provider returned empty audio")

        return SpeechSynthesisResult(
            audio=audio,
            media_type="audio/wav",
            voice=self.voice,
        )
