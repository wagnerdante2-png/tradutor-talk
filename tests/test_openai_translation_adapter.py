import asyncio
import json
from types import SimpleNamespace

from tradutor_talk.core.models import ConversationTurn, Direction
from tradutor_talk.providers.openai.translation import OpenAITranslationProvider


class FakeResponses:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(output_text="Bom dia")


class FakeClient:
    def __init__(self) -> None:
        self.responses = FakeResponses()


def test_translation_adapter_uses_bounded_structured_payload() -> None:
    async def run() -> None:
        client = FakeClient()
        provider = OpenAITranslationProvider(client=client)

        context = (
            ConversationTurn(
                direction=Direction.REMOTE_TO_LOCAL,
                source_language="en-US",
                target_language="pt-BR",
                original_text="Yesterday was busy.",
                translated_text="Ontem foi corrido.",
            ),
        )

        result = await provider.translate(
            text="Good morning",
            source_language="en-US",
            target_language="pt-BR",
            context=context,
            glossary={"WMS": "WMS"},
        )

        assert result.text == "Bom dia"
        assert result.source_language == "en-US"
        assert result.target_language == "pt-BR"

        kwargs = client.responses.kwargs
        assert kwargs["model"] == "gpt-5.6-luna"
        assert kwargs["reasoning"] == {"effort": "none"}
        assert kwargs["store"] is False

        payload = json.loads(kwargs["input"])
        assert payload["text"] == "Good morning"
        assert payload["glossary"] == {"WMS": "WMS"}
        assert len(payload["recent_context"]) == 1

    asyncio.run(run())
