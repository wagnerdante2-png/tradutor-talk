from __future__ import annotations

import argparse
import asyncio

from tradutor_talk.audio.capture import CaptureSettings, SoundDeviceRecorder
from tradutor_talk.infrastructure.config import load_config
from tradutor_talk.providers.openai.stt import OpenAISTTProvider


async def _run(seconds: float, language: str | None) -> None:
    config = load_config("config/default.toml")

    recorder = SoundDeviceRecorder(
        CaptureSettings(
            sample_rate=config.audio.sample_rate,
            channels=config.audio.channels,
            block_ms=config.audio.block_ms,
            dtype=config.audio.dtype,
        )
    )
    stt = OpenAISTTProvider(model=config.openai.stt_model)

    print(f"Gravando {seconds:.1f}s do microfone padrão...")
    wav = await recorder.record_wav(seconds)

    print(f"Áudio em memória: {len(wav)} bytes. Transcrevendo...")
    transcript = await stt.transcribe(wav, language_hint=language)

    print(f"Idioma: {transcript.detected_language}")
    print(f"Texto: {transcript.text}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Teste controlado de microfone + STT"
    )
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument(
        "--language",
        default=None,
        help="Idioma opcional, por exemplo pt-BR ou en-US",
    )
    args = parser.parse_args()

    if args.seconds <= 0 or args.seconds > 30:
        parser.error("--seconds deve estar entre 0 e 30")

    asyncio.run(_run(args.seconds, args.language))


if __name__ == "__main__":
    main()
