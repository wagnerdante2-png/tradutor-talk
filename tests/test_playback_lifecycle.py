import asyncio

import pytest

from tradutor_talk.core.models import Direction, SessionState, UtteranceStatus
from tradutor_talk.core.session import PlaybackLifecycleError, SessionBusyError, SessionController
from tradutor_talk.providers.mock import MockSTTProvider, MockTTSProvider, MockTranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary


def _controller() -> SessionController:
    controller = SessionController(
        stt=MockSTTProvider(),
        translator=MockTranslationProvider(),
        tts=MockTTSProvider(),
        context=ConversationContext(max_turns=4),
        glossary=Glossary(),
        provider_timeout_seconds=1,
    )
    controller.start()
    return controller


def _turn(controller: SessionController):
    return controller.process_audio(
        audio=b"Good morning",
        direction=Direction.REMOTE_TO_LOCAL,
        source_language="en-US",
        target_language="pt-BR",
    )


def test_second_turn_is_blocked_until_real_playback_finishes() -> None:
    async def run() -> None:
        controller = _controller()
        result = await _turn(controller)

        with pytest.raises(SessionBusyError):
            await _turn(controller)

        controller.begin_playback(result.utterance)

        with pytest.raises(SessionBusyError):
            await _turn(controller)

        controller.finish_playback(result.utterance)
        assert controller.state is SessionState.LISTENING

    asyncio.run(run())


def test_playback_failure_enters_error_and_can_recover() -> None:
    async def run() -> None:
        controller = _controller()
        result = await _turn(controller)

        controller.begin_playback(result.utterance)
        controller.fail_playback(result.utterance)

        assert result.utterance.status is UtteranceStatus.FAILED
        assert controller.state is SessionState.SESSION_ERROR

        controller.recover()
        assert controller.state is SessionState.LISTENING

    asyncio.run(run())


def test_finish_playback_rejects_wrong_lifecycle() -> None:
    async def run() -> None:
        controller = _controller()
        result = await _turn(controller)

        with pytest.raises(PlaybackLifecycleError):
            controller.finish_playback(result.utterance)

    asyncio.run(run())
