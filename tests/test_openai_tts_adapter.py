import asyncio
from types import SimpleNamespace

from tradutor_talk.providers.openai.tts import OpenAITTSProvider


class FakeSpeech:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=b"RIFFfake-wav")


class FakeClient:
    def __init__(self) -> None:
        self.speech = FakeSpeech()
        self.audio = SimpleNamespace(speech=self.speech)


def test_tts_adapter_returns_wav_bytes() -> None:
    async def run() -> None:
        client = FakeClient()
        provider = OpenAITTSProvider(client=client)

        result = await provider.synthesize(
            text="Bom dia",
            language="pt-BR",
        )

        assert result.audio == b"RIFFfake-wav"
        assert result.media_type == "audio/wav"
        assert result.voice == "marin"

        kwargs = client.speech.kwargs
        assert kwargs["model"] == "gpt-4o-mini-tts"
        assert kwargs["voice"] == "marin"
        assert kwargs["input"] == "Bom dia"
        assert kwargs["response_format"] == "wav"
        assert "pt-BR" in kwargs["instructions"]

    asyncio.run(run())
