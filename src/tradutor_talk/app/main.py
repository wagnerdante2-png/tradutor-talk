import asyncio

from tradutor_talk.app.bootstrap import build_mock_app
from tradutor_talk.core.models import Direction


async def _demo() -> None:
    app = build_mock_app()
    app.start()

    examples = [
        (b"Good morning", Direction.REMOTE_TO_LOCAL, "en-US", "pt-BR"),
        ("Bom dia".encode("utf-8"), Direction.LOCAL_TO_REMOTE, "pt-BR", "en-US"),
    ]

    print("Tradutor Talk — M0 deterministic demo")
    print(f"state={app.state.value}")

    for audio, direction, source, target in examples:
        result = await app.process_audio(
            audio=audio,
            direction=direction,
            source_language=source,
            target_language=target,
        )
        print(
            f"{direction.value}: {result.utterance.original_text!r} "
            f"→ {result.utterance.translated_text!r} "
            f"({result.utterance.total_latency_ms:.1f} ms)"
        )

    app.stop()
    print(f"state={app.state.value}")


def main() -> None:
    asyncio.run(_demo())
