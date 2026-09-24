import asyncio

from tradutor_talk.core.models import Direction, SessionState
from tradutor_talk.core.session import SessionController
from tradutor_talk.providers.mock import MockSTTProvider, MockTTSProvider, MockTranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary
from tradutor_talk.web.session import BrowserConversationSession


def _controller() -> SessionController:
    return SessionController(
        stt=MockSTTProvider(),
        translator=MockTranslationProvider(),
        tts=MockTTSProvider(),
        context=ConversationContext(max_turns=4),
        glossary=Glossary(),
        provider_timeout_seconds=1,
    )


def test_browser_session_waits_for_browser_playback_confirmation() -> None:
    async def run() -> None:
        web_session = BrowserConversationSession(controller_factory=_controller)

        result = await web_session.process_turn(
            audio=b"Good morning",
            direction=Direction.REMOTE_TO_LOCAL,
            source_language="en-US",
            target_language="pt-BR",
        )

        assert result.utterance.translated_text == "Bom dia"
        assert web_session.state == SessionState.PLAYING.value
        assert web_session.pending_utterance_id == result.utterance.id
        assert web_session.context_turns == 1

        await web_session.finish_playback(result.utterance.id)

        assert web_session.state == SessionState.LISTENING.value
        assert web_session.pending_utterance_id is None

    asyncio.run(run())


def test_browser_session_reset_clears_context() -> None:
    async def run() -> None:
        web_session = BrowserConversationSession(controller_factory=_controller)
        result = await web_session.process_turn(
            audio=b"Good morning",
            direction=Direction.REMOTE_TO_LOCAL,
            source_language="en-US",
            target_language="pt-BR",
        )
        await web_session.finish_playback(result.utterance.id)
        assert web_session.context_turns == 1

        await web_session.reset(clear_context=True)

        assert web_session.state == SessionState.LISTENING.value
        assert web_session.context_turns == 0

    asyncio.run(run())
