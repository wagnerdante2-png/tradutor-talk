import asyncio
from types import SimpleNamespace

from tradutor_talk.providers.openai.stt import OpenAISTTProvider


class FakeTranscriptions:
    def __init__(self) -> None:
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            text="Hello world",
            languages=[SimpleNamespace(code="en")],
        )


class FakeClient:
    def __init__(self) -> None:
        self.transcriptions = FakeTranscriptions()
        self.audio = SimpleNamespace(transcriptions=self.transcriptions)


def test_openai_stt_adapter_uses_in_memory_wav_and_language_hint() -> None:
    async def run() -> None:
        client = FakeClient()
        provider = OpenAISTTProvider(client=client)

        result = await provider.transcribe(
            b"RIFFfake",
            language_hint="en-US",
        )

        assert result.text == "Hello world"
        assert result.detected_language == "en"
        assert client.transcriptions.kwargs["model"] == "gpt-transcribe"
        assert client.transcriptions.kwargs["file"].name == "utterance.wav"
        assert client.transcriptions.kwargs["extra_body"] == {
            "languages": ["en"]
        }

    asyncio.run(run())
