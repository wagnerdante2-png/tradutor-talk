from __future__ import annotations

import asyncio
from io import BytesIO

from tradutor_talk.core.models import Transcript


class OpenAISTTProvider:
    def __init__(self, *, model: str = "gpt-transcribe", client=None) -> None:
        self.model = model
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

    async def transcribe(self, audio: bytes, *, language_hint: str | None = None) -> Transcript:
        if not audio:
            raise ValueError("audio cannot be empty")

        audio_file = BytesIO(audio)
        audio_file.name = "utterance.wav"
        kwargs = {"model": self.model, "file": audio_file}

        if language_hint:
            base_language = language_hint.split("-", 1)[0].lower()
            kwargs["extra_body"] = {"languages": [base_language]}

        client = self._client_or_create()
        response = await asyncio.to_thread(client.audio.transcriptions.create, **kwargs)

        text = str(getattr(response, "text", "")).strip()
        if not text:
            raise RuntimeError("STT provider returned empty transcript")

        detected_language = self._detected_language(response) or language_hint or "und"
        return Transcript(text=text, detected_language=detected_language, confidence=None)

    @staticmethod
    def _detected_language(response) -> str | None:
        languages = getattr(response, "languages", None) or []
        if not languages:
            return None
        first = languages[0]
        if isinstance(first, dict):
            return first.get("code")
        return getattr(first, "code", None)
