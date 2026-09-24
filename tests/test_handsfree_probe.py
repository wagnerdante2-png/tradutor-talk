import asyncio

import pytest

from tradutor_talk.app.handsfree_probe import _listen_and_translate
from tradutor_talk.core.models import Direction, SessionState
from tradutor_talk.core.session import SessionController
from tradutor_talk.providers.mock import MockSTTProvider, MockTTSProvider, MockTranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary


class FakeRecorder:
    async def wait_for_utterance_wav(self) -> bytes:
        return b"Good morning"


class FakePlayer:
    def __init__(self, controller: SessionController, *, fail: bool = False) -> None:
        self.controller = controller
        self.fail = fail
        self.calls = 0

    async def play_wav(self, audio: bytes) -> None:
        self.calls += 1
        assert audio == b"Bom dia"
        assert self.controller.state is SessionState.PLAYING
        if self.fail:
            raise RuntimeError("simulated playback failure")


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


def test_handsfree_turn_reopens_listening_only_after_playback() -> None:
    async def run() -> None:
        controller = _controller()
        player = FakePlayer(controller)

        await _listen_and_translate(
            label="INTERLOCUTOR",
            recorder=FakeRecorder(),
            player=player,
            controller=controller,
            direction=Direction.REMOTE_TO_LOCAL,
            source_language="en-US",
            target_language="pt-BR",
        )

        assert player.calls == 1
        assert controller.state is SessionState.LISTENING

    asyncio.run(run())


def test_handsfree_playback_failure_recovers_session() -> None:
    async def run() -> None:
        controller = _controller()
        player = FakePlayer(controller, fail=True)

        with pytest.raises(RuntimeError, match="simulated playback failure"):
            await _listen_and_translate(
                label="INTERLOCUTOR",
                recorder=FakeRecorder(),
                player=player,
                controller=controller,
                direction=Direction.REMOTE_TO_LOCAL,
                source_language="en-US",
                target_language="pt-BR",
            )

        assert controller.state is SessionState.LISTENING

    asyncio.run(run())
