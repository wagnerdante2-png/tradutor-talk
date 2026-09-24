from pathlib import Path

from tradutor_talk.core.session import SessionController
from tradutor_talk.infrastructure.config import AppConfig, load_config
from tradutor_talk.providers.mock import (
    MockSTTProvider,
    MockTTSProvider,
    MockTranslationProvider,
)
from tradutor_talk.providers.openai.stt import OpenAISTTProvider
from tradutor_talk.providers.openai.translation import OpenAITranslationProvider
from tradutor_talk.providers.openai.tts import OpenAITTSProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary


def _session_parts(config: AppConfig) -> tuple[ConversationContext, Glossary]:
    return (
        ConversationContext(max_turns=config.context.max_turns),
        Glossary.load(config.glossary.path),
    )


def build_mock_app(
    config_path: str | Path = "config/default.toml",
) -> SessionController:
    config = load_config(config_path)
    context, glossary = _session_parts(config)

    return SessionController(
        stt=MockSTTProvider(),
        translator=MockTranslationProvider(),
        tts=MockTTSProvider(),
        context=context,
        glossary=glossary,
        provider_timeout_seconds=config.session.provider_timeout_seconds,
    )


def build_openai_app(
    config_path: str | Path = "config/default.toml",
) -> SessionController:
    config = load_config(config_path)
    context, glossary = _session_parts(config)

    return SessionController(
        stt=OpenAISTTProvider(model=config.openai.stt_model),
        translator=OpenAITranslationProvider(
            model=config.openai.translation_model,
            reasoning_effort=config.openai.translation_reasoning_effort,
        ),
        tts=OpenAITTSProvider(
            model=config.openai.tts_model,
            voice=config.openai.tts_voice,
        ),
        context=context,
        glossary=glossary,
        provider_timeout_seconds=config.session.provider_timeout_seconds,
    )
