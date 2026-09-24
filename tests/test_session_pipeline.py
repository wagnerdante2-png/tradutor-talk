import asyncio

from tradutor_talk.core.models import Direction, SessionState, UtteranceStatus
from tradutor_talk.core.session import SessionController
from tradutor_talk.providers.mock import MockSTTProvider, MockTTSProvider, MockTranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary


def test_mock_pipeline_completes_and_returns_to_listening() -> None:
    async def run() -> None:
        controller = SessionController(
            stt=MockSTTProvider(),
            translator=MockTranslationProvider(),
            tts=MockTTSProvider(),
            context=ConversationContext(max_turns=4),
            glossary=Glossary(),
            provider_timeout_seconds=1,
        )
        controller.start()
        result = await controller.process_audio(
            audio=b"Good morning",
            direction=Direction.REMOTE_TO_LOCAL,
            source_language="en-US",
            target_language="pt-BR",
        )
        assert result.utterance.original_text == "Good morning"
        assert result.utterance.translated_text == "Bom dia"
        assert result.utterance.status is UtteranceStatus.COMPLETED
        assert result.speech.audio == b"Bom dia"
        assert controller.state is SessionState.LISTENING
        assert len(controller.context) == 1
        assert set(result.utterance.stage_latency_ms) == {"stt", "translation", "tts"}

    asyncio.run(run())
