from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from time import perf_counter
from typing import TypeVar

from tradutor_talk.core.models import ConversationTurn, Direction, ProcessResult, SessionState, Utterance, UtteranceStatus
from tradutor_talk.core.state_machine import SessionStateMachine
from tradutor_talk.providers.base import STTProvider, TTSProvider, TranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary

T = TypeVar("T")


class OperationCancelled(RuntimeError):
    pass


class ProviderTimeoutError(TimeoutError):
    pass


class SessionController:
    """Half-duplex session orchestrator with bounded context and cancellable providers."""

    def __init__(self, *, stt: STTProvider, translator: TranslationProvider, tts: TTSProvider,
                 context: ConversationContext, glossary: Glossary, provider_timeout_seconds: float = 10.0) -> None:
        self.stt = stt
        self.translator = translator
        self.tts = tts
        self.context = context
        self.glossary = glossary
        self.provider_timeout_seconds = provider_timeout_seconds
        self.state_machine = SessionStateMachine()
        self._lock = asyncio.Lock()
        self._cancel_event = asyncio.Event()

    @property
    def state(self) -> SessionState:
        return self.state_machine.state

    def start(self) -> None:
        if self.state is SessionState.IDLE:
            self.state_machine.transition(SessionState.LISTENING)

    def stop(self) -> None:
        self._cancel_event.set()
        self.state_machine.reset(SessionState.IDLE)

    def cancel_current(self) -> None:
        self._cancel_event.set()

    async def _stage(self, name: str, awaitable: Awaitable[T], utterance: Utterance) -> T:
        started = perf_counter()
        provider_task = asyncio.create_task(awaitable)
        cancel_task = asyncio.create_task(self._cancel_event.wait())
        try:
            done, _ = await asyncio.wait(
                {provider_task, cancel_task},
                timeout=self.provider_timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if not done:
                provider_task.cancel()
                raise ProviderTimeoutError(f"{name} exceeded {self.provider_timeout_seconds}s")
            if cancel_task in done and cancel_task.result():
                provider_task.cancel()
                raise OperationCancelled(f"{name} cancelled")
            result = await provider_task
            utterance.stage_latency_ms[name] = (perf_counter() - started) * 1000
            return result
        finally:
            cancel_task.cancel()
            if not provider_task.done():
                provider_task.cancel()

    async def process_audio(self, *, audio: bytes, direction: Direction,
                            source_language: str, target_language: str) -> ProcessResult:
        if not audio:
            raise ValueError("audio cannot be empty")
        if self.state is SessionState.IDLE:
            raise RuntimeError("session must be started before processing audio")

        async with self._lock:
            self._cancel_event.clear()
            utterance = Utterance(direction=direction, source_language=source_language, target_language=target_language)
            try:
                self.state_machine.transition(SessionState.SPEECH_DETECTED)
                self.state_machine.transition(SessionState.CAPTURING)
                self.state_machine.transition(SessionState.END_OF_TURN)
                self.state_machine.transition(SessionState.TRANSCRIBING)
                transcript = await self._stage("stt", self.stt.transcribe(audio, language_hint=source_language), utterance)
                utterance.original_text = transcript.text
                utterance.detected_language = transcript.detected_language
                utterance.status = UtteranceStatus.TRANSCRIBED

                self.state_machine.transition(SessionState.TRANSLATING)
                translated = await self._stage(
                    "translation",
                    self.translator.translate(
                        text=transcript.text,
                        source_language=transcript.detected_language or source_language,
                        target_language=target_language,
                        context=self.context.snapshot(),
                        glossary=self.glossary.as_mapping(),
                    ),
                    utterance,
                )
                utterance.translated_text = translated.text
                utterance.status = UtteranceStatus.TRANSLATED
                self.context.add(ConversationTurn(
                    direction=direction,
                    source_language=translated.source_language,
                    target_language=translated.target_language,
                    original_text=utterance.original_text,
                    translated_text=utterance.translated_text,
                ))

                self.state_machine.transition(SessionState.SYNTHESIZING)
                speech = await self._stage(
                    "tts",
                    self.tts.synthesize(text=utterance.translated_text, language=target_language),
                    utterance,
                )
                utterance.status = UtteranceStatus.SYNTHESIZED
                self.state_machine.transition(SessionState.PLAYING)
                self.state_machine.transition(SessionState.COOLDOWN)
                utterance.status = UtteranceStatus.COMPLETED
                utterance.finished_at = perf_counter()
                self.state_machine.transition(SessionState.LISTENING)
                return ProcessResult(utterance=utterance, speech=speech)

            except OperationCancelled:
                utterance.status = UtteranceStatus.CANCELLED
                utterance.finished_at = perf_counter()
                self.state_machine.reset(SessionState.LISTENING)
                raise
            except Exception:
                utterance.status = UtteranceStatus.FAILED
                utterance.finished_at = perf_counter()
                self.state_machine.transition(SessionState.SESSION_ERROR)
                raise
