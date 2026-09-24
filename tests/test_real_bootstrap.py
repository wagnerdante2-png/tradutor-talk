from tradutor_talk.app.bootstrap import build_openai_app
from tradutor_talk.providers.openai.stt import OpenAISTTProvider
from tradutor_talk.providers.openai.translation import OpenAITranslationProvider
from tradutor_talk.providers.openai.tts import OpenAITTSProvider


def test_real_bootstrap_composes_configured_providers_without_network() -> None:
    app = build_openai_app()

    assert isinstance(app.stt, OpenAISTTProvider)
    assert isinstance(app.translator, OpenAITranslationProvider)
    assert isinstance(app.tts, OpenAITTSProvider)

    assert app.stt.model == "gpt-transcribe"
    assert app.translator.model == "gpt-5.6-luna"
    assert app.translator.reasoning_effort == "none"
    assert app.tts.model == "gpt-4o-mini-tts"
    assert app.tts.voice == "marin"
