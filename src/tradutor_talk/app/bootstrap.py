from pathlib import Path

from tradutor_talk.core.session import SessionController
from tradutor_talk.infrastructure.config import AppConfig, load_config
from tradutor_talk.providers.mock import MockSTTProvider, MockTTSProvider, MockTranslationProvider
from tradutor_talk.translation.context import ConversationContext
from tradutor_talk.translation.glossary import Glossary


def build_mock_app(config_path: str | Path = "config/default.toml") -> SessionController:
    config: AppConfig = load_config(config_path)
    context = ConversationContext(max_turns=config.context.max_turns)
    glossary = Glossary.load(config.glossary.path)
    return SessionController(
        stt=MockSTTProvider(),
        translator=MockTranslationProvider(),
        tts=MockTTSProvider(),
        context=context,
        glossary=glossary,
        provider_timeout_seconds=config.session.provider_timeout_seconds,
    )
