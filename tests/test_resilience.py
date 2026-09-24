import asyncio

import pytest

from tradutor_talk.core.models import Direction, SessionState, Transcript
from tradutor_talk.core.session import (
    OperationCancelled,
    ProviderTimeoutError,
    SessionBusyError,
    SessionController,
)
from tradutor_talk.providers.mock import MockTTSProvider, MockTranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary


class SlowSTT:
    def __init__(self, delay: float) -> None:
        self.delay = delay

    async def transcribe(self, audio: bytes, *, language_hint: str | None = None) -> Transcript:
        await asyncio.sleep(self.delay)
        return Transcript(text="Good morning", detected_language=language_hint or "en-US", confidence=1.0)


def _controller(delay: float, timeout: float = 1.0) -> SessionController:
    return SessionController(
        stt=SlowSTT(delay),
        translator=MockTranslationProvider(),
        tts=MockTTSProvider(),
        context=ConversationContext(),
        glossary=Glossary(),
        provider_timeout_seconds=timeout,
    )


def _args() -> dict:
    return {
        "audio": b"audio",
        "direction": Direction.REMOTE_TO_LOCAL,
        "source_language": "en-US",
        "target_language": "pt-BR",
    }


def test_stop_during_provider_finishes_idle() -> None:
    async def run() -> None:
        controller = _controller(delay=10)
        controller.start()
        task = asyncio.create_task(controller.process_audio(**_args()))
        await asyncio.sleep(0)
        controller.stop()
        with pytest.raises(OperationCancelled):
            await task
        assert controller.state is SessionState.IDLE

    asyncio.run(run())


def test_busy_session_rejects_second_utterance_instead_of_queueing() -> None:
    async def run() -> None:
        controller = _controller(delay=10)
        controller.start()
        first = asyncio.create_task(controller.process_audio(**_args()))
        await asyncio.sleep(0)
        with pytest.raises(SessionBusyError):
            await controller.process_audio(**_args())
        controller.cancel_current()
        with pytest.raises(OperationCancelled):
            await first
        assert controller.state is SessionState.LISTENING

    asyncio.run(run())


def test_timeout_enters_error_and_explicit_recover_restores_listening() -> None:
    async def run() -> None:
        controller = _controller(delay=0.1, timeout=0.01)
        controller.start()
        with pytest.raises(ProviderTimeoutError):
            await controller.process_audio(**_args())
        assert controller.state is SessionState.SESSION_ERROR
        controller.recover()
        assert controller.state is SessionState.LISTENING

    asyncio.run(run())
